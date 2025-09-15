from mcp.server.fastmcp import FastMCP
from pydantic import Field
from mcp_microscopetoolset.utils import agent_message, user_message
from local.prepare_code import prepare_code


def create_mcp_server(
        microscope_session_object,
        database_agent,
        microscope_status,
        classify_agent,
        no_coding_agent,
        strategy_agent,
        software_agent,
        executor,
        logger_agent
):
    mcp = FastMCP(
        name="Microscope Toolset",
        host="127.0.0.1",
        port=5500,
        streamable_http_path="/mcp"
    )

    # define tools
    @mcp.tool(
        name="retrieve_db_context",
        description="This is the tool starts the feedback loop of the Microscope Toolset server. This tool retrieves "
                    "the information contained in the database that are the most relevant to the user main question. "
                    "It first reformulate the user query, then it use it in an hybrid search where a BM25 a KNN search"
                    "is performed. Finally, a rerank of the result is done using a cross-encoder and the top relevant "
                    "information are obtained. In addition you get a dictionary containing the information about the"
                    "status of the microscope like all the properties of the microscope, the current values selected"
                    "from the properties of the microscope and the configuration groups provided in the configuration"
                    "file."
                    "You always call first this tool at the start of the feedback."
    )
    def retrieve_db_context(
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
        # Get current settings
        microscope_status_response = microscope_status.get_current_status()
        # Get configuration settings
        config_settings = microscope_status.get_available_configs()
        microscope_status_settings = {
            "properties": microscope_properties_response,
            "current_status": microscope_status_response,
            "configuration_settings": config_settings
        }
        # update microscope status
        log_conversation = data_dict['conversation'] + [
            agent_message("Retrieved all the properties from the microscope."),
            agent_message("Retrieved the current system state properties."),
            agent_message("Retrieved the Configuration Groups with their Presets values!")
        ]
        microscope_session_object.update_data_dict(microscope_status=microscope_status_settings,
                                                   conversation=log_conversation)

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
    def classify_user_intent():
        """
        Call the internal intent classification logic.
        Returns a dictionary with 'intent' and 'message' (if clarification is needed).
        """
        # Get data dict of the session
        data_dict = microscope_session_object.get_data_dict()
        classify_user_query = classify_agent.classify_user_intent(data_dict)
        # add conversation
        loc_conversation = data_dict['conversation'] + [agent_message(classify_user_query["message"])]
        # update conversation
        microscope_session_object.update_data_dict(conversation=loc_conversation)
        return classify_user_query["message"]

    @mcp.tool(
        name="answer_no_coding_query",
        description="This tool is part of the feedback loop of the Microscope Toolset. It provides a direct answer to a "
                    "user query that does not require code generation. This tool will be called if the classify agent tool "
                    "classify the user's query as a 'no code needed'."
    )
    def answer_no_coding_query():
        """Uses the NoCodingAgent to generate an answer for non-code-related queries."""
        # Get data dict of the session
        data_dict = microscope_session_object.get_data_dict()
        # final output
        output = no_coding_agent.no_coding_answer(data_dict)
        # update data dict values
        microscope_session_object.update_data_dict(is_final_output=True, output=output["message"])
        # update is final output
        # data_dict['is_final_output'] = True
        # update output values
        # data_dict['output'] = output
        # update the microscope session object
        # microscope_session_object.reset_data_dict(old_output=output, old_microscope_status=data_dict['microscope_status'])

        return output["message"]  # check which type of answer is given

    @mcp.tool(
        name="generate_strategy",
        description="This tool is part of the feedback loop of the Microscope Toolset. It generates a strategic plan for "
                    "solving a user's question, especially for coding tasks. This tool will be called if the classify agent tool "
                    "classify the user's query as a 'propose strategy'. The user then will decide if the strategy proposed is good enough for answering the question. If the user doesn't agree"
                    "with the strategy proposed, the user will add the missing information."
    )
    def generate_strategy(additional_information: str = None):
        """
        Calls the StrategyAgent to generate a strategy.
        Return a json object with 'intent' (strategy/need_information) and 'message'
        """
        if additional_information is None:
            # Get data dict of the session
            data_dict = microscope_session_object.get_data_dict()
            strategy = strategy_agent.generate_strategy(data_dict)
            loc_conversation = data_dict['conversation'] + [agent_message(strategy["message"])]
        else:
            # update values
            microscope_session_object.update_data_dict(extra_infos=additional_information)
            # get current data dict
            data_dict = microscope_session_object.get_data_dict()
            strategy = strategy_agent.revise_strategy(data_dict)
            loc_conversation = data_dict['conversation'] + [user_message(additional_information),
                                                            agent_message(strategy["message"])]

        # update main strategy
        microscope_session_object.update_data_dict(main_agent_strategy=strategy["message"],
                                                   conversation=loc_conversation)

        return strategy["message"]

    @mcp.tool(
        name="generate_code",
        description="This tool is part of the feedback loop of the Microscope Toolset. It generates Python code based on "
                    "the current strategy and context. In addition, you could receive also the error produced by the code "
                    "you wrote. If this is the case you will need to fix your implementation."
    )
    def generate_code():
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
        loc_conversation = data_dict['conversation'] + [agent_message(code["message"])]
        microscope_session_object.update_data_dict(code=code["message"], conversation=loc_conversation)

        return code["message"]

    @mcp.tool(
        name="execute_python_code",
        description="This tool is part of the feedback loop of the Microscope Toolset. It executes a given Python code "
                    "string and returns its output or any errors. Once the code is successfully, show the result to the user. "
                    "Please always ask if the user query was answered or not (typically 'correct' or 'wrong') and save it "
                    "in the logger database"
    )
    def execute_python_code() -> dict:
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
    def show_result():
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
                                                      old_microscope_status=data_dict['microscope_status'])

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


def run_server(mcp: FastMCP):

    mcp.run(transport="streamable-http")