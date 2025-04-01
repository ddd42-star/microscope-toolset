# Run the application
import sys
import os
from python.execute import Execute
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI
from agents.main_agent import MainAgent
from agents.database_agent import DatabaseAgent
from agents.prompt_agent import PromptAgent
from agents.software_agent import SoftwareEngeneeringAgent
from agents.reasoning_agent import ReasoningAgent
from microscope.microscope_status import MicroscopeStatus
from pages.chat import chat
import threading


def main():
    # the input should be like this
    # python microscope-toolset --cfg <cfg name> --api_key <LLM key> --database <path to database> 
    # python microscope-toolset --cfg <cfg name> --api_key --database <path to database> 
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
            #get API key from system

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

    # start the program
    print("Welcome to Microscope-toolset!!\n\n")

    # Instancied the namespace
    executor = Execute(path_cfg_file)  # maybe refactor where user can put their instance object (?)

    # get the status of the microscope
    microscopeStatus = MicroscopeStatus(executor=executor)

    # initialize the thread
    monitor_thread = threading.Thread(target= microscopeStatus.monitor, daemon=True)
    monitor_thread.start()

    while True:

        menu_option = input(
            "------------------------------------\n"
            "Please select your available options:\n"
            "1)     start\n"
            "2)     exit\n"
            "------------------------------------\n"
            "command: ").lower()

        if menu_option == "start":

            # start tracking
            microscopeStatus._start = False
            # call the database
            openai_key = os.getenv("OPENAI_API_KEY")  # after change with dict of API keys
            api_ef = embedding_functions.OpenAIEmbeddingFunction(api_key=openai_key,
                                                                 model_name="text-embedding-3-small")

            chroma_client = chromadb.PersistentClient(path=path_database_file)

            client_collection = select_collection(chroma_client)

            # try that the collection contains all needed data
            try:
                print("The current database contains the following data:\n")
                print(client_collection.peek())
            except Exception as e:
                print("The database doesn't contain the needed data! Adjust it and retry.")
                sys.exit(e)

            # instantiate openai
            client_openai = OpenAI(api_key=openai_key)

            # get the status of the microscope
            #microscopeStatus = MicroscopeStatus(executor=executor)

            status = microscopeStatus.getCurrentStatus()  # dictonary with the current configuration values
            print("###########################################################\n")
            print("Currently the microscope has the current configurations:\n")
            print(status)
            print("###########################################################\n")

            # TODO checks that all the module of the requirement.txt are installed

            # The user may start to interact with LLM
            print("THE MICROSCOPE IS READY")
            print("-----------------------")
            print("THE LLM IS READY")
            print("-----------------")
            # Instance the Main Agent
            mainAgent = MainAgent(client_openai=client_openai)
            print("REFORMULATE AGENT IS READY")
            print("-----------------")
            # Instance the Database agent
            dbAgent = DatabaseAgent(client_openai=client_openai, chroma_client=chroma_client,
                                    client_collection=client_collection)
            print("DATABASE AGENT IS READY")
            print("-----------------")
            # instance the prompt Agent
            promptAgent = PromptAgent()
            print("PROMPT AGENT IS READY")
            print("-----------------")
            # Instance the Software Engeneering Agent
            softwareEngeneeringAgent = SoftwareEngeneeringAgent(client_openai=client_openai)
            print("SOFTWARE ENGENEERING AGENT IS READY")
            print("-----------------")
            # Instance the Reasoning Agent
            reAcAgent = ReasoningAgent(client_openai=client_openai)
            print("REASONING AGENT IS READY")
            print("-----------------")

            # change to chat page
            menu = ""
            while menu != "quit":
                menu = chat(mainAgent=mainAgent,
                            dbAgent=dbAgent,
                            promptAgent=promptAgent,
                            codeAgent=softwareEngeneeringAgent,
                            reacAgent=reAcAgent,
                            executor=executor,
                            microscopeStatus=microscopeStatus)

            # exit the loop

        elif menu_option == "exit":
            executor.is_running = False
            monitor_thread.join()
            sys.exit("See you next time!")
        else:
            print(""
                  "Invalid option! Please select between this options:\n"
                  "1)     start\n"
                  "2)     exit"
                  "-------------------------------------")


def select_collection(client: chromadb.ClientAPI) -> chromadb.Collection:
    """This function allow to select the available collection from the database"""
    # show available collection
    list_of_collection = client.list_collections()

    while True:
        collection_name = input(f"The available collection are {list_of_collection}, please select one: ")

        if collection_name in list_of_collection:
            break
        else:
            print("The collection doesn't exit! Please select one available option.")

    return client.get_collection(name=collection_name)


if __name__ == "__main__":
    # run the program
    main()
