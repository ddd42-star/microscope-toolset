# main.py
import asyncio
from openai import OpenAI
from typing import Any

# Import your core agents (needed to initialize the server's agents)
from agentsNormal.database_agent import DatabaseAgent
from agentsNormal.software_agent import SoftwareEngeneeringAgent
from agentsNormal.strategy_agent import StrategyAgent
from agentsNormal.error_agent import ErrorAgent
from agentsNormal.no_coding_agent import NoCodingAgent
from agentsNormal.classify_user_intent import ClassifyAgent
from microscope.microscope_status import MicroscopeStatus
from postqrl.connection import DBConnection
from postqrl.log_db import LoggerDB
import chromadb
from agentsNormal.logger_agent import LoggerAgent
from local_coding.execute import Execute
from dotenv import load_dotenv
import os
from mcp_microscopetoolset.mcp_orchestrator import initialize_orchestrator
from mcp_microscopetoolset.main_agent import MainAgent
from pymmcore_plus import CMMCorePlus
import napari

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


    return mmc

def load_config_file(config_file: str,mmc: CMMCorePlus.instance()):
    """This function load the config file added directly in napari micromanager"""
    mmc.loadSystemConfiguration(fileName=config_file)

    return None

def is_config_loaded():
    """This function listen to napari events has test if the configuration file has been loaded"""

    return None

async def run_application():
    # 1. Get Information of the user for the server (Which model,API_KEY, Datasets), just ask at the start the information and then cache it
    system_user_information = get_user_information()
    # Test database and cfg file
    executor = Execute(system_user_information['cfg_file'])
    #microscope_status = MicroscopeStatus(executor=executor)

    db_connection = DBConnection()

    db_log = LoggerDB(db_connection)

    chroma_client = chromadb.PersistentClient(path=system_user_information['database_path'])
    client_collection = chroma_client.get_collection(system_user_information['collection_name'])

    # client_openai = OpenAI(api_key=system_user_information['api_key'])
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

    # Instance the Classification Agent
    classification_agent = ClassifyAgent(client_openai=client_openai)

    initialize_orchestrator(
        openai_client=client_openai,
        db_agent=database_agent,
        software_agent=software_agent,
        strategy_agent=strategy_agent,
        error_agent=error_agent,
        no_coding_agent=no_coding_agent,
        executor=executor,
        logger_agent=logger_agent,
        classification_agent=classification_agent
    )
    print("All server components initialized.")

    # Initialize the MainAgent (client wrapper)
    main_agent = MainAgent()

    # start mmc core instance
    mmc = initiate_napari_micromanager()

    # load config file
    load_config_file(config_file=system_user_information['cfg_file'], mmc=mmc)

    print("Welcome! How can I help you today? (Type 'exit' to quit, 'reset' to start fresh)")

    while True:
        user_input = input("User: ")
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break

        # Process the user query. MainAgent will now send it to the server's orchestrator tool.
        llm_response = await main_agent.process_query(user_query=user_input)

        # Print the natural language response received from the server
        print(f"Main Agent: {llm_response}")

        # Check if the conversation is considered complete by the server
        if main_agent.is_conversation_complete():
            print(f"Final output: {main_agent.get_final_output()}")
            print("\nConversation completed. Type a new query or 'exit' to quit.")
            main_agent.reset_conversation()


if __name__ == "__main__":
    asyncio.run(run_application())