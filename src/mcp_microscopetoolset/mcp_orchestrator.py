import asyncio
import uuid
from mcp.server.fastmcp import FastMCP
from openai import OpenAI
from pydantic import Field
from mcp_microscopetoolset.utils import agent_message, user_message, tool_message, _add_to_conversation, mcp_to_openai
from mcp_microscopetoolset.mcp_tool import mcp_server as internal_mcp_tool
from mcp_microscopetoolset.mcp_tool import initialize_mcp_tool_agents
import json
import copy

mcp_orchestrator = FastMCP("Microscope orchestrator")

_orchestrator_llm_client: OpenAI = None
_active_session: dict[str, dict] = {}


def initialize_orchestrator(openai_client: OpenAI, db_agent, software_agent, strategy_agent,
                            error_agent, no_coding_agent, executor, logger_agent, classification_agent):
    global _orchestrator_llm_client
    _orchestrator_llm_client = openai_client
    initialize_mcp_tool_agents(db_agent, software_agent, strategy_agent, error_agent, no_coding_agent,
                               executor, openai_client, logger_agent, classification_agent)


def _get_initial_context():
    return {
        "user_query": "",
        "current_user_input": "",
        "conversation": [],
        "context": "",
        "extra_infos": "",
        "microscope_status": {},
        "previous_outputs": "",
        "main_agent_strategy": None,
        "new_strategy_proposed": False,
        "code": None,
        "error": None,
        "error_analysis": None,
        "is_final_output": False,
        "output": None,
        "clarification_needed_from_user": False,
        "approval_needed_from_user": False,
        "is_request_responded": False
    }
def _reset_context(old_output, old_microscope_status):
    return {
        "user_query": "",
        "current_user_input": "",
        "conversation": [],
        "context": "",
        "extra_infos": "",
        "microscope_status": old_microscope_status,
        "previous_outputs": old_output,
        "main_agent_strategy": None,
        "new_strategy_proposed": False,
        "code": None,
        "error": None,
        "error_analysis": None,
        "is_final_output": False,
        "output": None,
        "clarification_needed_from_user": False,
        "approval_needed_from_user": False,
        "is_request_responded": False
    }


async def orchestrate_turn(session_context: dict):
    """
        Internal function where the orchestrator LLM decides the next step
        based on the current session context and available tools.
        This replaces your original FSM logic.
        """
    system_prompt = (
        "You are an AI assistant managing a complex coding and problem-solving workflow. "
        "Your goal is to guide the user through the process using the available tools. "
        "Based on the conversation history and current context, decide which tool to call next, "
        "or if you need to ask the user for more information or approval or feedback. "
        "If you ask the user for clarification or approval or feedback, set the corresponding flags in the session_context. "
        "If the task is completed, ensure 'is_final_output' is set to True in the session_context. "
        "Respond with a natural language message for the user at the end of each turn, "
        "or indicate that you are performing an internal action."
        "\n\nAvailable tools (descriptions and parameters are crucial for your decision making):"
    )

    tool_definitions = await internal_mcp_tool.list_tools()

    # transform the List[Tool] into a OpenAI function
    tools_list_openai = [mcp_to_openai(tool) for tool in tool_definitions]

    messages_for_llm = [
                           {"role": "system", "content": system_prompt},
                           {"role": "system", "content": f"Current Session Context: {session_context}"},
                       ] + session_context["conversation"]

    llm_response_text = ""
    max_tool_calls = 50  # Prevent infinite loops in case of LLM going crazy
    tool_call_count = 0

    while tool_call_count < max_tool_calls:
        #print(messages_for_llm)
        orchestrator_llm_response = _orchestrator_llm_client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages_for_llm,
            tools=tools_list_openai,# change for openai tools_definition
            tool_choice="auto"
        )

        response_message = orchestrator_llm_response.choices[0].message
        print("This is the response of the LLM", response_message)
        if response_message.tool_calls:
            tool_call_count += 1
            tool_call = response_message.tool_calls[0]
            tool_name = tool_call.function.name
            tool_args = tool_call.function.arguments
            # add tool call message
            messages_for_llm.append({"role": "assistant", "tool_calls": response_message.tool_calls})

            print(f"DEBUG (Orchestrator): LLM decided to call tool: {tool_name} with args: {tool_args}")

            callable_args = {}
            if tool_name == "retrieve_db_context":
                callable_args = {
                    "user_query": session_context["current_user_input"]
                }
            elif tool_name in ["classify_user_intent","answer_no_coding_query", "generate_strategy", "revise_strategy",
                               "generate_code", "fix_code", "analyze_errors"]:
                callable_args = {"data_dict": session_context}
            elif tool_name == "execute_python_code":
                callable_args = {"code_string": session_context["code"]}
            elif tool_name == "save_result":
                callable_args = {"data_dict": session_context, "user_query": session_context["current_user_input"]}
            print("callable args: ", callable_args)
            try:
                tool_result = await internal_mcp_tool.call_tool(tool_name, callable_args)
                messages_for_llm.append(tool_message(tool_call.id,tool_name, tool_result[0].text))
                if tool_name == "retrieve_db_context":
                    session_context["context"] = tool_result[0].text
                    messages_for_llm.append(agent_message("I have retrieved relevant context."))
                    # maybe add to the conversation history
                elif tool_name == "classify_user_intent":
                    tool_result = json.loads(tool_result[0].text)
                    intent = tool_result["intent"]
                    message = tool_result["message"]
                    if intent == "ask_for_info":
                        session_context["clarification_needed_from_user"] = True
                        llm_response_text = message
                        break  # Break to ask user
                    elif intent == 'propose_strategy':
                        # The LLM will now likely call generate_strategy
                        #messages_for_llm.append(agent_message(message))
                        messages_for_llm.append(agent_message("I am determining the best strategy."))
                    elif intent == 'no_code_needed':
                        # The LLM will now likely call answer_no_code_query
                        #messages_for_llm.append(agent_message(message))
                        messages_for_llm.append(agent_message("This query does not require coding."))


                elif tool_name == "answer_no_code_query":
                    tool_result = json.loads(tool_result[0].text)
                    session_context["output"] = tool_result["message"]
                    session_context["is_final_output"] = True
                    llm_response_text = f"Here is the answer: {tool_result["message"]}"
                    break  # Final output
                elif tool_name == "generate_strategy":
                    tool_result = json.loads(tool_result[0].text)
                    session_context["main_agent_strategy"] = tool_result["message"]
                    # LLM should now ask for user approval
                    session_context["approval_needed_from_user"] = True
                    llm_response_text = f"Here is the proposed strategy:\n{tool_result["message"]}\nDo you approve? (yes/no)"
                    break  # Break to ask user
                elif tool_name == "revise_strategy":
                    tool_result = json.loads(tool_result[0].text)
                    session_context["main_agent_strategy"] = tool_result["message"]  # Update main strategy
                    session_context["new_strategy_proposed"] = True
                    # LLM should now proceed to code generation/fix
                    #messages_for_llm.append(agent_message(tool_result.message))
                    messages_for_llm.append(agent_message("Strategy revised. Moving to code generation/fix."))

                elif tool_name == "generate_code" or tool_name == "fix_code":
                    tool_result = json.loads(tool_result[0].text)
                    session_context["code"] = tool_result["message"]
                    # LLM should now call execute_python_code
                    #messages_for_llm.append(agent_message(tool_result.message))
                    messages_for_llm.append(agent_message("Code generated. Executing..."))

                elif tool_name == "execute_python_code":
                    tool_result = json.loads(tool_result[0].text)
                    if tool_result.get("status") == "success":
                        session_context["output"] = tool_result["output"]
                        # LLM should ask the user if the user's query was answered
                        session_context["is_request_responded"] = True
                        #session_context["is_final_output"] = True
                        llm_response_text = f"Code executed successfully. Output:\n{tool_result["output"]}\nWas your question answered? (correct/wrong)"
                        break
                    else:
                        session_context["error"] = tool_result["output"]
                        # LLM should now call analyze_error
                        #messages_for_llm.append(agent_message(tool_result.output))
                        messages_for_llm.append(agent_message("Code execution failed. Analyzing error..."))

                elif tool_name == "analyze_errors":
                    tool_result = json.loads(tool_result[0].text)
                    session_context["error_analysis"] = tool_result["message"]
                    session_context["new_strategy_proposed"] = True  # Indicate need for strategy revision
                    # LLM should now call revise_strategy
                    #messages_for_llm.append(agent_message(tool_result.message))
                    messages_for_llm.append(agent_message("Error analyzed. Attempting to revise strategy/code."))

                elif tool_name == "save_result":
                    session_context["is_final_output"] = True
                    break  # Final output

                # If LLM doesn't explicitly break, it means it needs to continue
                # and call another tool or generate text.
                # The while loop will continue by asking the LLM again.
            except Exception as e:
                print(e)
                error_info = f"Error executing tool '{tool_name}': {e}"
                messages_for_llm.append(tool_message(tool_call.id,tool_name, error_info))
                messages_for_llm.append(
                    agent_message("An error occurred during tool execution. Please stand by while I analyze it."))
                llm_response_text = "I encountered an issue. I'm trying to recover."
                # LLM will try to fix the error in the next turn
                break  # Break to let the user know, then LLM can self-correct

        else:
            llm_response_text = response_message.content
            # Check if LLM explicitly states task completion
            if "task completed" in llm_response_text.lower() or "final answer" in llm_response_text.lower():
                session_context["is_final_output"] = True
                session_context["output"] = llm_response_text  # Assuming final output is the text itself
            break  # LLM has decided to directly respond to the user
    if not llm_response_text:
        llm_response_text = "I'm processing your request. Please wait."

    return llm_response_text


@mcp_orchestrator.tool(
    name="process_user_request",
    description="Processes a user's request, managing the entire conversational flow and task execution. This is the primary entry point for all user interactions."
)
async def process_user_request(
        session_id: str = Field(
            description="Unique identifier for the current conversation session. Provide a new UUID for the first message of a new conversation, or 'new' to generate a new ID."),
        user_input: str = Field(description="The user's message or response in the current turn of the conversation.")
) -> dict:
    """
    This tool is the main entry point to the server. It orchestrates the entire
    multi-turn conversation by managing session context and invoking the internal
    orchestrator LLM to decide on actions.
    """
    # 1. Manage Session Context
    if session_id == "new" or session_id not in _active_session:
        session_id = str(uuid.uuid4())
        session_context = _get_initial_context()
        #print(session_context)
        _active_session[session_id] = session_context
        print(f"DEBUG: New session '{session_id}' initialized.")
    elif session_id == "reset":
        old_context = _active_session[session_id]
        session_id = str(uuid.uuid4())
        session_context = _reset_context(old_context["output"], old_context["microscope_status"])
        _active_session[session_id] = session_context
    else:
        session_context = _active_session[session_id]
        # Make a deep copy to ensure modifications are tracked and explicitly saved
        session_context = copy.deepcopy(session_context)

    session_context["current_user_input"] = user_input  # Store current input for LLM
    _add_to_conversation(session_context, "user", user_input)

    response_for_user = await orchestrate_turn(session_context)

    print("This is the response of the user", response_for_user)
    _active_session[session_id] = session_context

    final_response_for_client = {
        "session_id": session_id,
        "response_for_user": response_for_user,
        "is_conversation_final": session_context.get("is_final_output", False),
        "final_output_content": session_context.get("output")  # Only present if final
    }

    return final_response_for_client
