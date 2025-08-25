import os
import sys

import chromadb
from mcp.server.fastmcp import FastMCP

from openai import OpenAI
from pydantic import Field

from agentsNormal.database_agent import DatabaseAgent
from agentsNormal.error_agent import ErrorAgent
from agentsNormal.logger_agent import LoggerAgent
from agentsNormal.no_coding_agent import NoCodingAgent
from agentsNormal.software_agent import SoftwareEngeneeringAgent
from agentsNormal.strategy_agent import StrategyAgent
from agentsNormal.classify_user_intent import ClassifyAgent
from local.prepare_code import prepare_code
from mcp_microscopetoolset.utils import get_user_information, user_message, agent_message, logger_database_exists
from local.execute import Execute

from mcp_microscopetoolset.microscope_session import MicroscopeSession
from microscope.microscope_status import MicroscopeStatus
from postqrl.connection import DBConnection
from postqrl.log_db import LoggerDB
from databases.elasticsearch_db import ElasticSearchDB
from transformers import AutoTokenizer, AutoModelForSequenceClassification


def build_server():
    # Create the mcp server
    mcp = FastMCP(
        name="Microscope Toolset",
        host="127.0.0.1",
        port=5500,
        streamable_http_path="/mcp"
    )
    # description="This server allows the user to controls a selected microscope via LLM.",
    # version="1.0.0",

    # Initialize the microscope session object
    microscope_session_object = MicroscopeSession()
    # create the data_dict that will contain the feedback loop information
    # data_dict = microscope_session_object.get_data_dict()

    # Get the information for the user
    system_user_information = get_user_information()

    # start executor and tracking of the microscope status
    executor = Execute(system_user_information['cfg_file'])
    microscope_status = MicroscopeStatus(executor=executor)

    # initialize Logger database and his connection
    db_connection = DBConnection()
    db_log = LoggerDB(db_connection)

    # check if the logger database already exist
    if not logger_database_exists(db_log, system_user_information['log_collection']):
        # it doesn't exist. We create a new one
        db_log.create_collection(system_user_information['log_collection'])
        print(f"A new collection named {system_user_information['log_collection']} has been created.")

    # initialize vector database
    # chroma_client = chromadb.PersistentClient(path=system_user_information['database_path'])
    # client_collection = chroma_client.get_collection(name=system_user_information['collection_name'])
    # initialize elasticsearch
    es_client = ElasticSearchDB()
    try_connection = 0

    while try_connection < 10:
        print("Trying connection...")
        # try to establish the connection
        if es_client.is_connected():
            # the client is connected successfully
            break
        elif not es_client.is_connected() and try_connection < 10:
            sys.exit("Could not connect to elasticsearch. Please make sure to start the server before starting")
        else:
            # not connect
            try_connection += 1
            # try new client
            es_client = ElasticSearchDB()

    # get relevant information for the db
    pdf_publication = system_user_information['pdf_collection_name']
    micromanager_collection = system_user_information['micromanager_devices_collection']
    api_collection = system_user_information['collection_name']

    # Load the cross-encoder for re-ranking
    # Load model directly
    model_name = "cross-encoder/ms-marco-MiniLM-L6-v2"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)

    # initialize LLM API
    client_openai = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    # initialize different Agents
    # database_agent = DatabaseAgent(client_openai=client_openai, chroma_client=chroma_client,
    #                                client_collection=client_collection, db_log=db_log,
    #                                db_log_collection_name=system_user_information['log_collection'])
    database_agent = DatabaseAgent(client_openai=client_openai, es_client=es_client, pdf_collection=pdf_publication,
                                   micromanager_collection=micromanager_collection, api_collection=api_collection,
                                   db_log=db_log, db_log_collection_name=system_user_information['log_collection'],
                                   tokenizer=tokenizer, model=model)

    software_agent = SoftwareEngeneeringAgent(client_openai=client_openai)

    # error_agent = ErrorAgent(client_openai=client_openai)

    strategy_agent = StrategyAgent(client_openai=client_openai)

    no_coding_agent = NoCodingAgent(client_openai=client_openai)

    logger_agent = LoggerAgent(client_openai=client_openai)

    classify_agent = ClassifyAgent(client_openai=client_openai)

    # loads the configuration files from the microscope
    # load_config_file(config_file=system_user_information['cfg_file'], mmc=mmc)  # maybe change later

    # define different tools
    @mcp.tool(
        name="retrieve_db_context",
        description="This is the tool starts the feedback loop of the Microscope Toolset server. This tool retrieves "
                    "the information contained in the database that are the most relevant to the user main question. "
                    "It first reformulate the user query, then it use it in an hybrid search where a BM25 a KNN search"
                    "is performed. Finally, a rerank of the result is done using a cross-encoder and the top relevant "
                    "information are obtained."
                    "You always call first this tool at the start of the feedback."
    )
    async def retrieve_db_context(
            user_query: str = Field(description="The user's starting query of the feedback loop.")):
        """
        Uses the DatabaseAgent to retrieve the context for answering the user's query.Uses the DatabaseAgent to retrieve the context for answering the user's query.
        """
        # Get current data_dict
        data_dict = microscope_session_object.get_data_dict()
        # Checks the user_query
        # if microscope_session_object.is_main_user_query():
        # call the database agent
        # context = database_agent.look_for_context(user_query)
        # First reformulate query
        reformulated_query = database_agent.rephrase_query(user_query)
        print(reformulated_query["message"])
        # The search the information in our database
        context = database_agent.look_for_context(reformulated_query["message"])
        # add conversation
        loc_conversation = data_dict['conversation'] + [user_message(user_query), agent_message(context)]
        # update the data_dict
        microscope_session_object.update_data_dict(user_query=reformulated_query["message"], context=context,
                                                   conversation=loc_conversation)
        # Get Properties of the microscope
        microscope_properties_response = microscope_status.get_properties()
        # update microscope
        loc_conversation = data_dict['conversation'] + [
            agent_message("Retrieved all the properties from the microscope")]
        microscope_session_object.update_data_dict(microscope_properties=microscope_properties_response,
                                                   conversation=loc_conversation)
        # Get current settings
        microscope_status_response = microscope_status.get_current_status()
        # update microscope
        loc_conversation = data_dict['conversation'] + [
            agent_message("Retrieved the current system state properties")]
        microscope_session_object.update_data_dict(microscope_status=microscope_status_response,
                                                   conversation=loc_conversation)
        # Get configuration settings
        config_settings = microscope_status.get_available_configs()
        # update conversation
        loc_conversation = data_dict['conversation'] + [
            agent_message("Retrieved the Configuration Groups with their Presets values!")
        ]
        microscope_session_object.update_data_dict(configuration_presets=config_settings, conversation=loc_conversation)


        return context

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
        classify_user_query = classify_agent.classify_user_intent(data_dict)
        # add conversation
        loc_conversation = data_dict['conversation'] + [agent_message(classify_user_query.message)]
        # update conversation
        microscope_session_object.update_data_dict(conversation=loc_conversation)
        return classify_user_query.message

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
        output = no_coding_agent.no_coding_answer(data_dict)
        # update data dict values
        microscope_session_object.update_data_dict(is_final_output=True, output=output.message)
        # update is final output
        # data_dict['is_final_output'] = True
        # update output values
        # data_dict['output'] = output
        # update the microscope session object
        # microscope_session_object.reset_data_dict(old_output=output, old_microscope_status=data_dict['microscope_status'])

        return output.message  # check which type of answer is given

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
            loc_conversation = data_dict['conversation'] + [agent_message(strategy.message)]
        else:
            # update values
            microscope_session_object.update_data_dict(extra_infos=additional_information)
            # get current data dict
            data_dict = microscope_session_object.get_data_dict()
            strategy = strategy_agent.revise_strategy(data_dict)
            loc_conversation = data_dict['conversation'] + [user_message(additional_information),
                                                            agent_message(strategy.message)]

        # update main strategy
        microscope_session_object.update_data_dict(main_agent_strategy=strategy.message, conversation=loc_conversation)

        return strategy.message

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
        loc_conversation = data_dict['conversation'] + [agent_message(code.message)]
        microscope_session_object.update_data_dict(code=code.message, conversation=loc_conversation)

        return code.message

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
            microscope_session_object.update_data_dict(error=f"Code preparation/execution failed: {e}",
                                                       conversation=loc_conversation)
            return {"status": "error", "output": f"Code preparation/execution failed: {e}"}

    # evaluate if 'analyze_error' will be needed

    # @mcp.tool(
    #     name="save_result",
    #     description="This tool is part of the feedback loop of the Microscope Toolset. After showing the result to the user, "
    #                 "it will be asked to the user if the answer obtained was correct. We want to save into a database the "
    #                 "correct and the wrong answer to help you to answer the future user's questions. After you successfully "
    #                 "completed this, the user will likely ask you others questions or stop the server."
    # )
    # async def save_result(user_query: str = Field(description="The user's response, typically 'correct' or 'wrong'.")):
    #     """
    #     Calls the LoggerAgent to save the output of the Agents into a database.
    #     Returns a json object with 'intent' (save) and a message.
    #     """
    #     # Get current data dict
    #     data_dict = microscope_session_object.get_data_dict()
    #     # evaluate user's answer
    #     if user_query == "correct":
    #         success = True
    #     elif user_query == "wrong":
    #         success = False
    #     else:
    #         loc_conversation = data_dict['conversation'] + [
    #             agent_message("Please specify if your query was answered or not using 'correct' or 'wrong'!")]
    #         microscope_session_object.update_data_dict(conversation=loc_conversation)
    #         return {"intent": 'error',
    #                 "message": "Please specify if your query was answered or not using 'correct' or 'wrong'!"}
    #     # prepare summary of the code
    #     summary_chat = logger_agent.prepare_summary(data_dict)
    #     if summary_chat.intent == "summary":
    #         data = {"prompt": summary_chat.message, "output": data_dict['code'], "feedback": success, "category": ""}
    #         # add into the db
    #         database_agent.add_log(data)
    #     # update the microscope session object
    #     microscope_session_object.reset_data_dict(old_output=data_dict['output'],
    #                                               old_microscope_status=data_dict['microscope_status'],
    #                                               old_microscope_properties=data_dict['microscope_properties'],
    #                                               old_microscope_presets=data_dict['configuration_presets'])
    #
    #     return {"intent": 'save', "message": "The previous result was added to the log database."}

    @mcp.tool(
        name="show_result",
        description="This tool is part of the feedback loop of the Microscope Toolset. Once the parameter 'is_final_output' "
                    "is changed to True, you need to show the user the final output."
    )
    async def show_result():
        """
        Shows the user the final output
        """
        # Get current data dict
        data_dict = microscope_session_object.get_data_dict()
        # show the final output
        if data_dict['is_final_output']:
            final_output = data_dict['output']
            # update conversation
            loc_conversation = data_dict['conversation'] + [agent_message(final_output)]
            microscope_session_object.update_data_dict(conversation=loc_conversation)
            # prepare summary of the code
            summary_chat = logger_agent.prepare_summary(data_dict)
            if summary_chat.intent == "summary":
                data = {"prompt": summary_chat.message, "output": data_dict['code'], "feedback": True,
                        "category": ""}
                # add into the db
                database_agent.add_log(data)
            # update the microscope session object
            microscope_session_object.reset_data_dict(old_output=data_dict['output'],
                                                      old_microscope_status=data_dict['microscope_status'],
                                                      old_microscope_properties=data_dict['microscope_properties'],
                                                      old_microscope_presets=data_dict['configuration_presets'])


            return final_output
        else:
            message = "The final output was not reach yet!"
            loc_conversation = data_dict['conversation'] + [agent_message(message)]
            microscope_session_object.update_data_dict(conversation=loc_conversation)
            return message

    # @mcp.tool(
    #     name="get_microscope_properties",
    #     description="This tool is part of the feedback loop of the Microscope Toolset.It retrieves all the properties of all the devices present in the microscope. Only retrieve once all the properties of the microscope during the feedback loop."
    # )
    # async def get_microscope_properties():
    #     """
    #     Retrieve all the properties of the microscope
    #     """
    #     # Get current data dict
    #     data_dict = microscope_session_object.get_data_dict()
    #
    #     microscope_properties_response = microscope_status.get_properties()
    #     # update microscope
    #     loc_conversation = data_dict['conversation'] + [
    #         agent_message("Retrieved all the properties from the microscope")]
    #     microscope_session_object.update_data_dict(microscope_properties=microscope_properties_response,
    #                                                conversation=loc_conversation)
    #     return microscope_properties_response

    # @mcp.tool(
    #     name="get_currently_microscope_status",
    #     description="This tool is part of the feedback loop of the Microscope Toolset.It retrieves the system state properties currently selected of the microscope."
    # )
    # async def get_currently_microscope_status():
    #     """
    #     Retrieve the current settings of the microscope
    #     """
    #     # Get current data dict
    #     data_dict = microscope_session_object.get_data_dict()
    #
    #     microscope_status_response = microscope_status.get_current_status()
    #     # update microscope
    #     loc_conversation = data_dict['conversation'] + [
    #         agent_message("Retrieved the current system state properties")]
    #     microscope_session_object.update_data_dict(microscope_status=microscope_status_response,
    #                                                conversation=loc_conversation)
    #     return microscope_status_response

    # @mcp.tool(
    #     name="get_config_settings",
    #     description="This tool is part of the feedback loop of the Microscope Toolset. It retrieves the Configuration Groups with the applied presets. Only retrieves once the Configuration Groups with their presets values."
    # )
    # async def get_config_settings():
    #     # Get current data
    #     data_dict = microscope_session_object.get_data_dict()
    #
    #     config_settings = microscope_status.get_available_configs()
    #     # update conversation
    #     loc_conversation = data_dict['conversation'] + [
    #         agent_message("Retrieved the Configuration Groups with their Presets values!")
    #     ]
    #     microscope_session_object.update_data_dict(configuration_presets=config_settings, conversation=loc_conversation)
    #     return config_settings

    return mcp


if __name__ == "__main__":
    # start sever
    try:
        mcp = build_server()
        mcp.run(transport="streamable-http")

    except KeyboardInterrupt:
        print("server interrupted by the user")
