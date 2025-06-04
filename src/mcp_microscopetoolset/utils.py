from pydantic import BaseModel, Field
from prompts.mainAgentPrompt import CLASSIFY_INTENT
from openai import OpenAI
from mcp.types import Tool

class AgentOutput(BaseModel):

    intent: str
    message: str

def parse_agent_response(response: str):

    try:
        return AgentOutput.model_validate_json(response)
    except Exception as e:
        return e


def user_message(message):

    return {"role": "user", "content": message}


def agent_message(message: str):

    return {"role": "assistant", "content": message}

def tool_message(tool_call_id: str,tool_name: str, content: str):
    return {"role": "tool", "tool_call_id": tool_call_id,"name": tool_name, "content": content}

def _add_to_conversation(context: dict, role: str, message: str):
    """Helper to add messages to the conversation history within the context."""
    context["conversation"].append({"role": role, "content": message})

def agent_action(client_openai: OpenAI, context: dict, prompt: str):

    history = [{"role": "system", "content": prompt}, {"role": "user", "content": context["user_query"]}] + context[
        "conversation"]

    response = client_openai.beta.chat.completions.parse(
        model="gpt-4.1-mini",
        messages=history,
        response_format=AgentOutput
    )

    return parse_agent_response(response.choices[0].message.content)

def mcp_to_openai(tool: Tool):
    """
    Transform a mcp tool into an openai function schema
    """
    return {
        "type":"function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.inputSchema,
            "strict": False
        }
    }