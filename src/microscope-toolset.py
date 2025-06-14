# Run the application
import logging

# configure logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# Create a file handler to save logs to a file
file_handler = logging.FileHandler('my_logs.log')
file_handler.setLevel(logging.INFO)  # Set log level for file (INFO and higher)

# Create a formatter for the file handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add the file handler to the root logger (not using basicConfig, but manually adding)
logging.getLogger().addHandler(file_handler)

import sys
import os
from local.execute import Execute
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI
# from agentsNormal.main_agent import MainAgent
from prompts.main_agent import MainAgentState
from agentsNormal.database_agent import DatabaseAgent
from agentsNormal.prompt_agent import PromptAgent
from agentsNormal.software_agent import SoftwareEngeneeringAgent
from agentsNormal.reasoning_agent import ReasoningAgent
from agentsNormal.error_agent import ErrorAgent
from agentsNormal.clarification_agent import ClarificationAgent
from agentsNormal.no_coding_agent import NoCodingAgent
from agentsNormal.strategy_agent import StrategyAgent
from agentsNormal.logger_agent import LoggerAgent
from microscope.microscope_status import MicroscopeStatus
import threading
from postqrl.connection import DBConnection
from postqrl.log_db import LoggerDB
from pages.states import START_PAGE, EXIT, MAIN_MENU, CHAT_PAGE, DATABASE
from pages.start import start_page
from pages.menu import menu, chat, database

# silence other annoying logs
logging.getLogger("chromadb").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("pymmcore-plus").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def main():
    # the input should be like this
    # local microscope-toolset --cfg <cfg name> --api_key <LLM key> --database <path to database>
    # local microscope-toolset --cfg <cfg name> --api_key --database <path to database>
    tot_arg = len(sys.argv) - 1

    list_arg = str(sys.argv)

    if "--cfg" not in list_arg:
        raise TypeError("missing --cfg keyword")

    if "--api_key" not in list_arg:
        raise TypeError("missing --api_key keyword")

    if "--database" not in list_arg:
        raise TypeError("missing --database keyword")

    try:
        # try to convert the input given in the command line
        path_cfg_file = str(sys.argv[2])

    except Exception as e:
        return e

    try:
        # get API key
        api_key_dict = {}
        if str(sys.argv[4]) == "--database":
            # get API key from system

            for i in ["OPENAI_API_KEY", "GEMINI_API_KEY", "OLLOMA_API_KEY", "ANTHROPIC_API_KEY"]:
                api_key_dict[i] = os.getenv(i)
                # TODO add part when the key is missing
                try:
                    # try to convert the input given in the command line
                    path_database_file = str(sys.argv[5])

                except Exception as e:
                    return e

        else:
            try:
                # get information about the api_key. Should be of a format of type_LLM:key
                llm, key = str(sys.argv[4].split(":"))
            except Exception as e:
                return e

            api_key_dict[llm] = key

            try:
                # try to convert the input given in the command line
                path_database_file = str(sys.argv[6])

            except Exception as e:
                return e

    except Exception as e:
        return e

    # TODO: put all the checks into a separate function

    # start the program
    mainLogger = logging.getLogger(__name__)
    mainLogger.info("Welcome to Microscope-toolset!!\n\n")

    # Instanced the namespace
    executor = Execute(path_cfg_file)  # maybe refactor where user can put their instance object (?)

    # get the status of the microscope
    microscopeStatus = MicroscopeStatus(executor=executor)

    # initialize the thread
    monitor_thread = threading.Thread(target=microscopeStatus.monitor, daemon=True)
    monitor_thread.start()

    # call the logger database
    db_connection = DBConnection()
    db_log = LoggerDB(db_connection)
    state = START_PAGE

    # start tracking
    microscopeStatus._start = False
    # call the database
    openai_key = os.getenv("OPENAI_API_KEY")  # after change with dict of API keys
    api_ef = embedding_functions.OpenAIEmbeddingFunction(api_key=openai_key,
                                                         model_name="text-embedding-3-small")

    chroma_client = chromadb.PersistentClient(path=path_database_file)
    # sleep
    # time.sleep(1)
    client_collection = select_collection(chroma_client)
    log_collection_name = select_log_collection(db_log)

    # try that the collection contains all needed data
    try:
        mainLogger.info("The current database contains the following data:\n")
        mainLogger.info(client_collection.peek())
    except Exception as e:
        mainLogger.error("The database doesn't contain the needed data! Adjust it and retry.")
        sys.exit(e)

    # instantiate openai
    client_openai = OpenAI(api_key=openai_key)
    # print(openai_key)
    # get the status of the microscope
    # microscopeStatus = MicroscopeStatus(executor=executor)

    status = microscopeStatus.getCurrentStatus()  # dictonary with the current configuration values
    mainLogger.info("""
    Currently the microscope has the current configurations:
    %s
    """, status)
    # print("###########################################################\n")
    # print("Currently the microscope has the current configurations:\n")
    # print(status)
    # print("###########################################################\n")

    # TODO checks that all the module of the requirement.txt are installed

    # The user may start to interact with LLM
    mainLogger.info("THE MICROSCOPE IS READY")
    # print("-----------------------")
    mainLogger.info("THE LLM IS READY")
    # print("-----------------")
    # Instance the Main Agent
    # mainAgent = MainAgent(client_openai=client_openai)
    # mainLogger.info("MAIN AGENT IS READY")
    # print("-----------------")
    # Instance the Database agent
    dbAgent = DatabaseAgent(client_openai=client_openai, chroma_client=chroma_client,
                            client_collection=client_collection, db_log=db_log,
                            db_log_collection_name=log_collection_name)
    mainLogger.info("DATABASE AGENT IS READY")
    # print("-----------------")
    # instance the prompt Agent
    promptAgent = PromptAgent()
    mainLogger.info("PROMPT AGENT IS READY")
    # print("-----------------")
    # Instance the Software Engeneering Agent
    softwareEngeneeringAgent = SoftwareEngeneeringAgent(client_openai=client_openai)
    mainLogger.info("SOFTWARE ENGENEERING AGENT IS READY")
    # print("-----------------")
    # Instance the Reasoning Agent
    reAcAgent = ReasoningAgent(client_openai=client_openai)
    mainLogger.info("REASONING AGENT IS READY")
    # print("-----------------")
    # Instance the Error Agent
    error_agent = ErrorAgent(client_openai=client_openai)
    mainLogger.info("ERROR AGENT IS READY")

    # Instance the Strategy Agent
    strategy_agent = StrategyAgent(client_openai=client_openai)
    mainLogger.info("STRATEGY AGENT IS READY")

    # Instance No coding agent
    no_coding_agent = NoCodingAgent(client_openai=client_openai)
    mainLogger.info("NO CODING AGENT IS READY")

    # Instance the Clarification Agent
    clarification_agent = ClarificationAgent(client_openai=client_openai)
    mainLogger.info("CLARIFICATION AGENT IS READY")

    # Instance the Logger Agent
    logger_agent = LoggerAgent(client_openai=client_openai)
    mainLogger.info("LOGGER AGENT IS READY")

    while state != EXIT:
        if state == START_PAGE:
            state = start_page()
        elif state == MAIN_MENU:
            state = menu()
        elif state == CHAT_PAGE:
            state = chat(executor=executor,client_openai=client_openai, dbAgent=dbAgent, softwareEngeneeringAgent=softwareEngeneeringAgent, reAcAgent=reAcAgent,
                 strategy_agent=strategy_agent, no_coding_agent=no_coding_agent,
                 clarification_agent=clarification_agent, error_agent=error_agent, log_agent=logger_agent)
        elif state == DATABASE:
            state = database(dbLog=db_log)

    executor.is_running = False
    monitor_thread.join()
    db_log.close()
    sys.exit("See you next time!")


def select_collection(client: chromadb.ClientAPI) -> chromadb.Collection:
    """This function allow to select the available collection from the database"""
    logger = logging.getLogger(__name__)
    # show available collection
    list_of_collection = client.list_collections()

    while True:
        collection_name = input(f"The available collection are {list_of_collection}, please select one: ")

        if collection_name in list_of_collection:
            break
        else:
            logger.info("The collection doesn't exit! Please select one available option.")

    return client.get_collection(name=collection_name)


def select_log_collection(db_connection: LoggerDB):
    """This function select the available log collection name from the database"""
    logger = logging.getLogger(__name__)
    # show available collection
    list_of_collection = db_connection.list_collection()
    if len(list_of_collection) == 0:  # empy list
        no_name = []
        return no_name
    while True:
        collection_name = input(f"The available log collection are {list_of_collection}, please select one: ")

        if collection_name in list_of_collection:
            break
        else:
            logger.info("The collection doesn't exist! Please select one available option.")

    return collection_name

#
# if __name__ == "__main__":
#     # run the program
#     main()
