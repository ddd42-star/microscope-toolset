import os
import asyncio
import sys

import chromadb
from mcp.server.fastmcp import FastMCP
import threading
import napari
from openai import OpenAI
from pydantic import Field
from pymmcore_plus import CMMCorePlus

from agentsNormal.clarification_agent import ClarificationAgent
from agentsNormal.database_agent import DatabaseAgent
from agentsNormal.error_agent import ErrorAgent
from agentsNormal.logger_agent import LoggerAgent
from agentsNormal.no_coding_agent import NoCodingAgent
from agentsNormal.reasoning_agent import ReasoningAgent
from agentsNormal.software_agent import SoftwareEngeneeringAgent
from agentsNormal.strategy_agent import StrategyAgent
from local.prepare_code import prepare_code
from mcp_microscopetoolset.utils import get_user_information, initiate_napari_micromanager, load_config_file, \
    is_config_loaded, AgentOutput, parse_agent_response, user_message, agent_message
from local.execute import Execute

from mcp_microscopetoolset.microscope_session import MicroscopeSession
from microscope.microscope_status import MicroscopeStatus
from postqrl.connection import DBConnection
from postqrl.log_db import LoggerDB
from prompts.mainAgentPrompt import CLASSIFY_INTENT

# Create the mcp server
mcp = FastMCP(
    name="Microscope Toolset",
    description="This server allows the user to controls a selected microscope via LLM.",
    version="1.0.0"
)

# Initialize the microscope session object
microscope_session_object = MicroscopeSession()
# create the data_dict that will contain the feedback loop information
#data_dict = microscope_session_object.get_data_dict()

# Get the information for the user
system_user_information = get_user_information()

# start executor and tracking of the microscope status
executor = Execute(system_user_information['cfg_file'])
microscope_status = MicroscopeStatus(executor=executor)

# initialize Logger database and his connection
db_connection = DBConnection()
db_log = LoggerDB(db_connection)

# initialize vector database
chroma_client = chromadb.PersistentClient(path=system_user_information['database_path'])
client_collection = chroma_client.get_collection(name=system_user_information['collection_name'])


# initialize LLM API
client_openai = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# initialize different Agents
database_agent = DatabaseAgent(client_openai=client_openai, chroma_client=chroma_client,
                               client_collection=client_collection, db_log=db_log,
                               db_log_collection_name=system_user_information['log_collection'])

software_agent = SoftwareEngeneeringAgent(client_openai=client_openai)

reasoning_agent = ReasoningAgent(client_openai=client_openai)

error_agent = ErrorAgent(client_openai=client_openai)

strategy_agent = StrategyAgent(client_openai=client_openai)

no_coding_agent = NoCodingAgent(client_openai=client_openai)

clarification_agent = ClarificationAgent(client_openai=client_openai)

logger_agent = LoggerAgent(client_openai=client_openai)

# Initialize Napari gui
#mmc, viewer = initiate_napari_micromanager()

# loads the configuration files from the microscope
#load_config_file(config_file=system_user_information['cfg_file'], mmc=mmc)  # maybe change later


# define different tools
@mcp.tool(
    name="retrieve_db_context",
    description="This is the tool starts the feedback loop of the Microscope Toolset server. This tool retrieves "
                "the information contained in the vector database that are the most relevant to the user main question. "
                "You always call first this tool at the start of the feedback."
)
async def retrieve_db_context(user_query: str = Field(description="The user's starting query of the feedback loop.")):
    """
    Uses the DatabaseAgent to retrieve the context for answering the user's query.Uses the DatabaseAgent to retrieve the context for answering the user's query.
    """
    # Get current data_dict
    data_dict = microscope_session_object.get_data_dict()
    # Checks the user_query
    if microscope_session_object.is_main_user_query():
        # call the database agent
        context = database_agent.look_for_context(user_query)
        # add conversation
        loc_conversation = data_dict['conversation'] + [user_message(user_query), agent_message(context)]
        # update the data_dict
        microscope_session_object.update_data_dict(user_query=user_query, context=context, conversation=loc_conversation)

        return context
    return "This is not the user main question. This tool is not indicated for your need."

@mcp.tool(
    name="classify_user_intent",
    description="This tool is part of the feedback loop of the Microscope Toolset. This tool helps to classify "
                "the intent ot the user from the user's main query. "
                "There are three possible classification:"
                "- ask for info: Given the information retrieved from the database and the user request, some information are missing to be able to answer correctly the user's question."
                "- propose strategy: The information retrieved from the database are sufficient to answer the user's main question and a strategy can be formulated by the Strategy Agent."
                "- no code needed: From the information retrieved from the vector database and the user's main question, you are able to understand that it doesn't need any sort of coding script for answering the user's main question. You can call the No Coding Agent."
                "This tool normally is always the second tool to call in the feedback loop."
)
async def classify_user_intent():
    """
    Call the internal intent classification logic.
    Returns a dictionary with 'intent' and 'message' (if clarification is needed).
    """
    # Get data dict of the session
    data_dict = microscope_session_object.get_data_dict()
    #specify parameters
    user_query = data_dict['user_query']
    context = data_dict['context']
    microscope_status = data_dict['microscope_status']
    previous_outputs = data_dict['previous_outputs']
    conversation_history = data_dict['conversation']

    prompt = CLASSIFY_INTENT.format(
        context=context or "no information",
        microscope_status=microscope_status or "no information",
        previous_outputs=previous_outputs or "no information"
    )

    history = [{"role": "system", "content": prompt}, {"role": "user", "content": user_query}] + conversation_history

    try:
        response = client_openai.beta.chat.completions.parse(
            model="gpt-4.1-mini",
            messages=history,
            response_format=AgentOutput
        )
        # parse response
        parsed_response = parse_agent_response(response.choices[0].message.content)
        # add conversation
        loc_conversation = conversation_history + [agent_message(parsed_response)]
        microscope_session_object.update_data_dict(conversation=loc_conversation)
        return parsed_response
    except Exception as e:
        return f"Failed to classify intent: {e}"


@mcp.tool(
    name="answer_no_coding_query",
    description="This tool is part of the feedback loop of the Microscope Toolset. It provides a direct answer to a "
                "user query that does not require code generation. This tool will be called if the classify agent tool "
                "classify the user's query as a 'no code needed'."
)
async def answer_no_coding_query():
    """Uses the NoCodingAgent to generate an answer for non-code-related queries."""
    # Get data dict of the session
    data_dict = microscope_session_object.get_data_dict()
    # final output
    output = no_coding_agent.no_coding_asnwer(data_dict)
    # update data dict values
    microscope_session_object.update_data_dict(is_final_output=True, output=output)
    # update is final output
    #data_dict['is_final_output'] = True
    # update output values
    #data_dict['output'] = output
    # update the microscope session object
    #microscope_session_object.reset_data_dict(old_output=output, old_microscope_status=data_dict['microscope_status'])

    return output # check which type of answer is given

@mcp.tool(
    name="generate_strategy",
    description="This tool is part of the feedback loop of the Microscope Toolset. It generates a strategic plan for "
                "solving a user's question, especially for coding tasks. This tool will be called if the classify agent tool "
                "classify the user's query as a 'propose strategy'. The user then will decide if the strategy proposed is good enough for answering the question. If the user doesn't agree"
                "with the strategy proposed, the user will add the missing information."
)
async def generate_strategy(additional_information: str = None):
    """
    Calls the StrategyAgent to generate a strategy.
    Return a json object with 'intent' (strategy/need_information) and 'message'
    """
    if additional_information is None:
        # Get data dict of the session
        data_dict = microscope_session_object.get_data_dict()
        strategy = strategy_agent.generate_strategy(data_dict)
        loc_conversation = data_dict['conversation'] + [agent_message(strategy)]
    else:
        #update values
        microscope_session_object.update_data_dict(extra_infos=additional_information)
        # get current data dict
        data_dict = microscope_session_object.get_data_dict()
        strategy = strategy_agent.revise_strategy(data_dict)
        loc_conversation = data_dict['conversation'] + [user_message(additional_information), agent_message(strategy)]

    # update main strategy
    microscope_session_object.update_data_dict(main_agent_strategy=strategy, conversation=loc_conversation)

    return strategy

@mcp.tool(
    name="generate_code",
    description="This tool is part of the feedback loop of the Microscope Toolset. It generates Python code based on "
                "the current strategy and context. In addition, you could receive also the error produced by the code "
                "you wrote. If this is the case you will need to fix your implementation."
)
async def generate_code():
    """
    Calls the SoftwareAgent to generate code.
    Return a json object with 'intent' (code) and 'message'
    """
    # Get current data dict
    data_dict = microscope_session_object.get_data_dict()
    if data_dict['error'] is None:
        code = software_agent.generate_code(data_dict)
    else:
        code = software_agent.fix_code(data_dict)

    # update code value
    loc_conversation = data_dict['conversation'] + [agent_message(code)]
    microscope_session_object.update_data_dict(code=code, conversation=loc_conversation)

    return code

@mcp.tool(
    name="execute_python_code",
    description="This tool is part of the feedback loop of the Microscope Toolset. It executes a given Python code "
                "string and returns its output or any errors. Once the code is successfully, show th result to the user. "
                "Please always ask if the user query was answered or not (typically 'correct' or 'wrong') and save it "
                "in the logger database"
)
async def execute_python_code() -> dict:
    """
    Prepares and executes Python code using the Execute agent.
    Returns a dictionary with 'output' (the execution result) and 'error' (if any).
    """
    # Get current data dict
    data_dict = microscope_session_object.get_data_dict()
    code_string = data_dict['code']
    try:
        prepare_code_to_run = prepare_code(code_string.strip("```"))
        execution_output = executor.run_code(prepare_code_to_run)
        if "Error" in execution_output:
            # update data dict
            loc_conversation = data_dict['conversation'] + [agent_message(execution_output)]
            microscope_session_object.update_data_dict(error=execution_output, conversation=loc_conversation)
            return {'status': 'error', 'output': execution_output}
        else:
            # update data dict and is final output
            microscope_session_object.update_data_dict(output=execution_output, is_final_output=True)
            return {'status': 'success', 'output': execution_output}
    except Exception as e:
        # update data dict value
        loc_conversation = data_dict['conversation'] + [agent_message(f"Code preparation/execution failed: {e}")]
        microscope_session_object.update_data_dict(error=f"Code preparation/execution failed: {e}", conversation=loc_conversation)
        return {"status": "error", "output": f"Code preparation/execution failed: {e}"}
# evaluate if 'analyze_error' will be needed

@mcp.tool(
    name="save_result",
    description="This tool is part of the feedback loop of the Microscope Toolset. After showing the result to the user, "
                "it will be asked to the user if the answer obtained was correct. We want to save into a database the "
                "correct and the wrong answer to help you to answer the future user's questions. After you successfully "
                "completed this, the user will likely ask you others questions or stop the server."
)
async def save_result(user_query: str = Field(description="The user's response, typically 'correct' or 'wrong'.")):
    """
    Calls the LoggerAgent to save the output of the Agents into a database.
    Returns a json object with 'intent' (save) and a message.
    """
    # Get current data dict
    data_dict = microscope_session_object.get_data_dict()
    # evaluate user's answer
    if user_query == "correct":
        success = True
    elif user_query == "wrong":
        success = False
    else:
        loc_conversation = data_dict['conversation'] + [agent_message("Please specify if your query was answered or not using 'correct' or 'wrong'!")]
        microscope_session_object.update_data_dict(conversation=loc_conversation)
        return {"intent": 'error', "message": "Please specify if your query was answered or not using 'correct' or 'wrong'!"}
    # prepare summary of the code
    summary_chat = logger_agent.prepare_summary(data_dict)
    if summary_chat.intent == "summary":
        data = {"prompt": summary_chat.message, "output": data_dict['code'], "feedback": success, "category": ""}
        # add into the db
        database_agent.add_log(data)
    # update the microscope session object
    microscope_session_object.reset_data_dict(old_output=data_dict['output'], old_microscope_status=data_dict['microscope_status'])

    return {"intent": 'save', "message": "The previous result was added to the log database."}

@mcp.tool(
    name="show_result",
    description="to add"
)
async def show_result():
    "to add"
    # Get current data dict
    data_dict = microscope_session_object.get_data_dict()
    # show the final output
    if data_dict['is_final_output']:
        final_output = data_dict['output']
        # update conversation
        loc_conversation = data_dict['conversation'] + agent_message(final_output)
        microscope_session_object.update_data_dict(conversation=loc_conversation)
        return final_output
    else:
        message = "The final output was not reach yet!"
        loc_conversation = data_dict['conversation'] + [agent_message(message)]
        microscope_session_object.update_data_dict(conversation=loc_conversation)
        return message

def mcp_server():
    mcp.run(transport="stdio")

def run_gui():
    # Initialize Napari gui
    mmc, viewer = initiate_napari_micromanager()

    # loads the configuration files from the microscope
    load_config_file(config_file=system_user_information['cfg_file'], mmc=mmc)  # maybe change later

    napari.run()

if __name__ == "__main__":
    # run the mcp server into another thread
    thread_mcp_server = threading.Thread(name="MCP server", target=mcp_server)
    # start the thread
    thread_mcp_server.start()
    # run napari gui
    run_gui()
    #once the gui is closed, stop the thread of the mcp server
    # discover how to do it