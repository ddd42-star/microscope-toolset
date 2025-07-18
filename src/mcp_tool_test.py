import asyncio
from openai import OpenAI
from typing import Any
from agentsNormal.database_agent import DatabaseAgent
from agentsNormal.software_agent import SoftwareEngeneeringAgent
from agentsNormal.reasoning_agent import ReasoningAgent
from agentsNormal.strategy_agent import StrategyAgent
from agentsNormal.error_agent import ErrorAgent
from agentsNormal.no_coding_agent import NoCodingAgent
from agentsNormal.clarification_agent import ClarificationAgent
from microscope.microscope_status import MicroscopeStatus
from postqrl.connection import DBConnection
from postqrl.log_db import LoggerDB
import chromadb
from agentsNormal.logger_agent import LoggerAgent
from mcp_microscopetoolset.main_agent import MainAgent
from pymmcore_plus import CMMCorePlus
import napari
import mcp.types as types
from mcp.server.fastmcp import FastMCP
import os
from utils.normal_LLM import llm_prompt
from dotenv import load_dotenv
from local.execute import Execute
from pydantic import Field
from mcp_microscopetoolset.utils import parse_agent_response, AgentOutput
from prompts.mainAgentPrompt import CLASSIFY_INTENT
from local.prepare_code import prepare_code
from mcp_microscopetoolset.session_context import SessionContext

# add initialization components
def get_user_information() -> dict:
    """
    This function retrieves the user information from the system. Later we will add the possibility for the user to add it
    """
    user_information = {}
    # load user from the environment
    load_dotenv()

    user_information['model'] = os.getenv("model")
    user_information['api_key'] = os.getenv("API_KEY")
    user_information['database_path'] = os.getenv("DATABASE")
    user_information['collection_name'] = os.getenv("DBNAME")
    user_information['log_collection'] = os.getenv("LOGNAME")
    user_information['cfg_file'] = os.getenv("CFGPATH")

    return user_information

def initiate_napari_micromanager():
    """This function start the napari micromanager GUI and access the core instance"""

    viewer = napari.Viewer()
    # start the napari plugin
    dw, mainwindow = viewer.window.add_plugin_dock_widget(plugin_name="napari-micromanager")

    # access the instance core
    mmc = CMMCorePlus.instance()


    return mmc, viewer

def load_config_file(config_file: str,mmc: CMMCorePlus.instance()):
    """This function load the config file added directly in napari micromanager"""
    mmc.loadSystemConfiguration(fileName=config_file)

    return None

def is_config_loaded():
    """This function listen to napari events has test if the configuration file has been loaded"""

    return None


"""
Initialize the session with all the necessary components.
"""
# 1. Get Information of the user for the server (Which model,API_KEY, Datasets), just ask at the start the information and then cache it
system_user_information = get_user_information()

# Test database and cfg file
executor = Execute(system_user_information['cfg_file'])
microscope_status = MicroscopeStatus(executor=executor)

db_connection = DBConnection()

db_log = LoggerDB(db_connection)

chroma_client = chromadb.PersistentClient(path=system_user_information['database_path'])
client_collection = chroma_client.get_collection(system_user_information['collection_name'])

client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# get current status
status = microscope_status.getCurrentStatus()  # dictionary with the current configuration values

# initialize agents
# Initialize Agent
database_agent = DatabaseAgent(client_openai=client_openai, chroma_client=chroma_client,
                               client_collection=client_collection, db_log=db_log,
                               db_log_collection_name=system_user_information['log_collection'])
software_agent = SoftwareEngeneeringAgent(client_openai=client_openai)

reasoning_agent = ReasoningAgent(client_openai=client_openai)

error_agent = ErrorAgent(client_openai=client_openai)

# Instance the Strategy Agent
strategy_agent = StrategyAgent(client_openai=client_openai)

# Instance No coding agent
no_coding_agent = NoCodingAgent(client_openai=client_openai)

# Instance the Clarification Agent
clarification_agent = ClarificationAgent(client_openai=client_openai)

# Instance the Logger Agent
logger_agent = LoggerAgent(client_openai=client_openai)

mmc, viewer = initiate_napari_micromanager()

# load config file
load_config_file(config_file=system_user_information['cfg_file'], mmc=mmc)

# define Server
mcp_server = FastMCP("Tools Microscope")

@mcp_server.tool(
    name="classify_user_intent",
    description="Classifies the user's initial query to determine their intent (e.g., ask for info, propose strategy, no code needed)."
)
async def classify_user_intent(
        user_query: str = Field(description="The user's original query."),
        context: str = Field(description="Relevant context from the vector database."),
        microscope_status: dict = Field(description="Current microscope status, if any."),
        previous_outputs: str = Field(description="Previous outputs from the system, if any."),
        conversation_history: list = Field(description="Full conversation history.")):
    """
    Call the internal intent classification logic.
    Returns a dictionary with 'intent' and 'message' (if clarification is needed).
    """
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

        return parsed_response
    except Exception as e:
        return {"intent": "error", "message": f"Failed to classify intent: {e}"}


@mcp_server.tool(
    name="answer_no_coding_query",
    description="Provides a direct answer to a user query that does not require code generation."
)
async def answer_no_coding_query(
        data_dict: dict = Field(description="The current context dictionary of the main agent.")):
    """Uses the NoCodingAgent to generate an answer for non-code-related queries."""
    return no_coding_agent.no_coding_asnwer(data_dict)


@mcp_server.tool(
    name="generate_strategy",
    description="Generates a strategic plan for solving a user's request, especially for coding tasks."
)
async def generate_strategy(data_dict: dict = Field(description="The current context dictionary of the main agent.")):
    """
    Calls the StrategyAgent to generate a strategy.
    Return a json object with 'intent' (strategy/need_information) and 'message'
    """
    return strategy_agent.generate_strategy(data_dict)


@mcp_server.tool(
    name="revise_strategy",
    description="Revises an existing strategy based on new information or user feedback."
)
async def revise_strategy(data_dict: dict = Field(description="The current context dictionary of the main agent.")):
    """
    Calls the StrategyAgent to revise a strategy.
    Return a json object with 'intent' (new_strategy) and 'message'
    """
    return strategy_agent.revise_strategy(data_dict)


@mcp_server.tool(
    name="generate_code",
    description="Generates Python code based on the current strategy and context."
)
async def generate_code(data_dict: dict = Field(description="The current context dictionary of the main agent.")):
    """
    Calls the SoftwareAgent to generate code.
    Return a json object with 'intent' (code) and 'message'
    """
    return software_agent.generate_code(data_dict)


@mcp_server.tool(
    name="fix_code",
    description="Fixes existing Python code based on error analysis and context."
)
async def fix_code(data_dict: dict = Field(description="The current context dictionary of the main agent.")):
    """
    Calls the SoftwareAgent to fix the code.
    Return a json object with 'intent' (code) and 'message' (the fixed code string)
    """
    return software_agent.fix_code(data_dict)


@mcp_server.tool(
    name="execute_python_code",
    description="Executes a given Python code string and returns its output or any errors."
)
async def execute_python_code(code_string: str = Field(description="The Python code to execute, as a string.")) -> dict:
    """
    Prepares and executes Python code using the Execute agent.
    Returns a dictionary with 'output' (the execution result) and 'error' (if any).
    """
    try:
        prepare_code_to_run = prepare_code(code_string.strip("```"))
        execution_output = executor.run_code(prepare_code_to_run)
        if "Error" in execution_output:
            return {'status': 'error', 'output': execution_output}
        else:
            return {'status': 'success', 'output': execution_output}
    except Exception as e:
        return {"status": "error", "output": f"Code preparation/execution failed: {e}"}


@mcp_server.tool(
    name="analyze_errors",
    description="Analyzes an error message from code execution to provide insights for fixing the code."
)
async def analyze_errors(data_dict: dict = Field(description="The current context dictionary of the main agent.")):
    """
    Calls the ErrorAgent to analyze an error.
    Returns a json object with 'intent' (error_analysis) and 'message' (the analysis).
    """
    return error_agent.analyze_error(data_dict)


@mcp_server.tool(
    name="awaiting_user_approval",
    description="Processes a user's 'yes' or 'no' response for a previously asked approval."
)
async def awaiting_user_approval(user_query: str = Field(description="The user's response, typically 'yes' or 'no'.")):
    """
    Determines if the user approved an action.
    Returns a dictionary with 'approved': True/False and a message.
    """
    if user_query.lower() == "yes":
        return {"approved": True, "message": "User approved the action."}
    else:
        return {"approved": False, "message": "User did not approve the action."}


@mcp_server.tool(
    name="save_result",
    description="Create a summary of the conversation between the user and the agentic system after 'is_final_output' is set to True and add it to the specialized database."
)
async def save_result(data_dict: dict = Field(description="The current context dictionary of the main agent."),
                      user_query: str = Field(description="The user's response, typically 'correct' or 'wrong'.")):
    """
    Calls the LoggerAgent to save the output of the Agents into a database.
    Returns a json object with 'intent' (save) and a message.
    """
    # evaluate user's answer
    if user_query == "correct":
        success = True
    else:
        success = False
    # prepare summary of the code
    summary_chat = logger_agent.prepare_summary(data_dict)
    if summary_chat.intent == "summary":
        data = {"prompt": summary_chat.message, "output": data_dict['code'], "feedback": success, "category": ""}
        # add into the db
        database_agent.add_log(data)

    return {"intent": 'save', "message": "The previous result was added to the log database."}

if __name__ == "__main__":
    # Initialize and run the server
    mcp_server.run(transport='stdio')