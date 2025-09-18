from mcp.server.fastmcp import FastMCP
import os
from dotenv import load_dotenv
from local_coding.execute import Execute
from microscope.microscope_status import MicroscopeStatus
from postqrl.connection import DBConnection
from postqrl.log_db import LoggerDB
import chromadb
from openai import OpenAI
from agentsNormal.database_agent import DatabaseAgent
from agentsNormal.software_agent import SoftwareEngeneeringAgent
from agentsNormal.error_agent import ErrorAgent
from agentsNormal.strategy_agent import StrategyAgent
from agentsNormal.no_coding_agent import NoCodingAgent
from agentsNormal.logger_agent import LoggerAgent
from agentsNormal.classify_user_intent import ClassifyAgent
from mcp_microscopetoolset.mcp_orchestrator import initialize_orchestrator
from mcp_microscopetoolset.main_agent import MainAgent

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
# 1. Get Information of the user for the server (Which model,API_KEY, Datasets), just ask at the start the information and then cache it
system_user_information = get_user_information()
# Test database and cfg file
executor = Execute(system_user_information['cfg_file'])
#microscope_status = MicroscopeStatus(executor=executor)

db_connection = DBConnection()

db_log = LoggerDB(db_connection)

chroma_client = chromadb.PersistentClient(path=system_user_information['database_path'])
client_collection = chroma_client.get_collection(system_user_information['collection_name'])

#client_openai = OpenAI(api_key=system_user_information['api_key'])
client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# get current status
#status = microscope_status.get_current_status()  # dictonary with the current configuration values

# Initialize Agent
database_agent = DatabaseAgent(client_openai=client_openai, chroma_client=chroma_client,
                            client_collection=client_collection, db_log=db_log,
                            db_log_collection_name=system_user_information['log_collection'])
software_agent = SoftwareEngeneeringAgent(client_openai=client_openai)

error_agent = ErrorAgent(client_openai=client_openai)

# Instance the Strategy Agent
strategy_agent = StrategyAgent(client_openai=client_openai)

# Instance No coding agent
no_coding_agent = NoCodingAgent(client_openai=client_openai)

# Instance the Logger Agent
logger_agent = LoggerAgent(client_openai=client_openai)

classification_agent = ClassifyAgent(client_openai=client_openai)

main_agent = MainAgent()

#Initialize all client
initialize_orchestrator(
    client_openai,database_agent,software_agent, strategy_agent, error_agent, no_coding_agent, executor, logger_agent, classification_agent
)

# create server
#toolset_server = FastMCP(name="Microscope Toolset",main_agent=main_agent,log_agent=logger_agent)
toolset_server = FastMCP(name="Microscope Toolset")

@toolset_server.tool()
async def microscope_toolset(user_query: str):
    """
    This tools is a Microscope Assistant. It is a multi-agent system that can interact directly with a microscope.
    """
    # Steps
    #main_agent = toolset_server.settings.main_agent
    #log_agent = toolset_server.settings.log_agent

    response =  await main_agent.process_query(user_query=user_query)

    print(f'Main Agent: {response}')

    if main_agent.is_conversation_complete():
        return main_agent.get_final_output()

    return response



@toolset_server.tool()
def search_articles():

    return None


@toolset_server.tool()
def llm(user_input: str):
    """
    This tools is a simple agent that helps the user in any types of questions and requests

    Input:
        user_input: str
            Represent the user's question or request
    Output:
        A plane text string containing the API call of the agent.
    """
    openai_key = os.getenv("OPENAI_API_KEY")

    client = OpenAI(api_key=openai_key)

    prompt = """
You are a friendly assistant. Be always truthful and precise. You will receive any kind of request or question.
If is required be as scientific as possible
"""

    history = [{"role": "system", "content": prompt}, {"role": "user", "content": user_input}]

    try:

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=history
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Error communicating with LLM: {e}"


if __name__ == "__main__":
    # Initialize and run the server
    toolset_server.run(transport='stdio')


