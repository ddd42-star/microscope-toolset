from typing import Any, Dict, List
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from local.prepare_code import prepare_code


def create_mcp_server(
        database_agent,
        microscope_status,
        no_coding_agent,
        executor,
        logger_agent
) -> FastMCP:
    # Server definition
    mcp = FastMCP(
        name="Microscope Toolset",
        host="127.0.0.1",
        port=5500,
        streamable_http_path="/mcp"
    )

    @mcp.tool(
        name="pymmcore_api_database",
        description="This tool is part of the feedback loop of the Microscope Toolset. It will return the relevant information"
                    "from the API database of pymmcore_plus. The relevant information will be searched by an hybrid method using"
                    "the reformulated query. The hybrid method will use the BM25 text matching and KNN search using embedding"
                    "vectors. Afterwards, a cross encoder will re-rank the result obtained to match only the most top 25 relevant"
                    "chunks of information."
    )
    def pymmcore_api_database(
            user_query: str = Field(..., description="The user original question")
    ) -> dict[str, Any]:

        # reformulate user query
        reformulated_question = database_agent.rephrase_query(user_query)

        return database_agent.api_pymmcore_context(user_query, reformulated_question)

    @mcp.tool(
        name="micromanager_device_database",
        description="This tool is part of the feedback loop of the Microscope Toolset. It will return the relevant information"
                    "from the micromanager device. The relevant information will be searched by an hybrid method using"
                    "the reformulated query. The hybrid method will use the BM25 text matching and KNN search using embedding"
                    "vectors. Afterwards, a cross encoder will re-rank the result obtained to match only the most top 25 relevant"
                    "chunks of information."
    )
    def micromanager_device_database(
            user_query: str = Field(..., description="The user original question")
    ) -> dict[str, Any]:

        # reformulate user query
        reformulated_question = database_agent.rephrase_query(user_query)

        return database_agent.devices_micromanager_context(user_query, reformulated_question)

    @mcp.tool(
        name="pdfs_publication_database",
        description="This tool is part of the feedback loop of the Microscope Toolset. It will return the relevant information"
                    "from a collection of scientific publications. The relevant information will be searched by an hybrid method using"
                    "the reformulated query. The hybrid method will use the BM25 text matching and KNN search using embedding"
                    "vectors. Afterwards, a cross encoder will re-rank the result obtained to match only the most top 25 relevant"
                    "chunks of information."
    )
    def pdfs_publication_database(
            user_query: str = Field(..., description="The user original question")
    ) -> dict[str, Any]:

        # reformulate user query
        reformulated_question = database_agent.rephrase_query(user_query)

        return database_agent.pdf_publication_context(user_query, reformulated_question)

    # @mcp.tool(
    #     name="reformulate_user_query",
    #     description="This tool is part of the feedback loop of the Microscope Toolset. It is used to rephrase the user question"
    #                 "that starts the feedback loop. The reformulated query will be used to search into different databases to retrieve"
    #                 "important information using text match with BM25 and embedding vectors."
    # )
    # def reformulate_user_query(
    #         user_question: str = Field(..., description="The user original question")
    # ) -> dict[str, Any]:
    #     # add check that structured response is getting the correct answer
    #     return database_agent.rephrase_query(user_question)

    @mcp.tool(
        name="get_microscope_settings",
        description="This tool is part of the feedback loop of the Microscope Toolset. It has access to the settings of"
                    "a microscope. It returns a dictionary with the properties of the microscope, the current properties values "
                    "selected of each devices and the configuration groups saved into the microscope configuration file."
                    "This tool is useful to discover the properties and devices of the microscope."
    )
    def get_microscope_settings() -> dict[str, Any]:

        # Get Properties of the microscope
        microscope_properties_response = microscope_status.get_properties()
        # Get current settings
        microscope_status_response = microscope_status.get_current_status()
        # Get configuration settings
        config_settings = microscope_status.get_available_configs()
        microscope_status_settings = {
            "properties_schema": microscope_properties_response,
            "current_properties_status": microscope_status_response,
            "configuration_groups_settings": config_settings
        }

        return microscope_status_settings

    # @mcp.tool(
    #     name="classify_user_intent",
    #     description="This tool is part of the feedback loop of the Microscope Toolset. This tool helps to classify "
    #                 "the intent ot the user from the user's main query. "
    #                 "There are three possible classification:"
    #                 "- ask for info: Given the information retrieved from the database and the user request, some information are missing to be able to answer correctly the user's question."
    #                 "- propose strategy: The information retrieved from the database are sufficient to answer the user's main question and a strategy can be formulated by the Strategy Agent."
    #                 "- no code needed: From the information retrieved from the vector database and the user's main question, you are able to understand that it doesn't need any sort of coding script for answering the user's main question. You can call the No Coding Agent."
    #                 "This tool normally is always the second tool to call in the feedback loop."
    # )
    # def classify_user_intent(
    #         user_question: str = Field(..., description="The user original question"),
    #         reformulated_question: str = Field(..., description="The reformulated question")
    # ) -> dict[str, Any]:
    #     """
    #     Call the internal intent classification logic.
    #     Returns a dictionary with 'intent' and 'message' (if clarification is needed).
    #     """
    #     # Get data dict of the session
    #     #data_dict = microscope_session_object.get_data_dict()
    #     data_dict = {
    #         "user_query": user_question,
    #         "reformulated_query": reformulated_question
    #     }
    #     classify_user_query = classify_agent.classify_user_intent(data_dict)
    #     # add conversation
    #     # loc_conversation = data_dict['conversation'] + [agent_message(classify_user_query["message"])]
    #     # # update conversation
    #     # microscope_session_object.update_data_dict(conversation=loc_conversation)
    #     return classify_user_query

    @mcp.tool(
        name="answer_no_coding_query",
        description="This tool is part of the feedback loop of the Microscope Toolset. It provides a direct answer to a "
                    "user query that does not require code generation. This tool will be called if the classify agent tool "
                    "classify the user's query as a 'no code needed'."
    )
    def answer_no_coding_query(
            user_query: str = Field(..., description="The user original query")
    ):
        """Uses the NoCodingAgent to generate an answer for non-code-related queries."""
        # Get data dict of the session
        data_dict = {
            "user_query": user_query
        }
        # final output
        output = no_coding_agent.no_coding_answer(data_dict)

        return {
            "is_final_output": True,
            output: output["message"]
        } # check which type of answer is given

    # @mcp.tool(
    #     name="generate_strategy",
    #     description="This tool is part of the feedback loop of the Microscope Toolset. It generates a strategic plan for "
    #                 "solving a user's question, especially for coding tasks. This tool will be called if the classify agent tool "
    #                 "classify the user's query as a 'propose strategy'. The user then will decide if the strategy proposed is good enough for answering the question. If the user doesn't agree"
    #                 "with the strategy proposed, the user will add the missing information."
    # )
    # def generate_strategy(
    #         user_query: str = Field(..., description="The user original query"),
    #         reformulated_query: str = Field(..., description="The reformulated query"),
    #         context: List[Dict[str, Any]] = Field(..., description="The contextual information retrieved from the user's main question"),
    #         additional_information: str = Field(..., description="Additional information given by the user."),
    #         microscope_settings: Dict[str, Any] = Field(..., description="The microscope settings")
    # ) -> StrategyAgentOutput:
    #     """
    #     Calls the StrategyAgent to generate a strategy.
    #     Return a json object with the 'strategy'
    #     """
    #     data_dict = {
    #         "user_query": user_query,
    #         "reformulated_query": reformulated_query,
    #         "context": context,
    #         "additional_information": additional_information,
    #         "microscope_settings": microscope_settings
    #     }
    #     strategy = strategy_agent.generate_strategy(data_dict)
    #
    #     return strategy

    # @mcp.tool(
    #     name="generate_code",
    #     description="This tool is part of the feedback loop of the Microscope Toolset. It generates Python code based on "
    #                 "the current strategy and context. In addition, you could receive also the error produced by the code "
    #                 "you wrote. If this is the case you will need to fix your implementation."
    # )
    # def generate_code(
    #         user_query: str = Field(..., description="The user original query"),
    #         reformulated_query: str = Field(..., description="The reformulated query"),
    #         context: List[Dict[str, Any]] = Field(..., description="The contextual information retrieved from the user's main question"),
    #         additional_information: str = Field(..., description="Additional information given by the user."),
    #         microscope_settings: Dict[str, Any] = Field(..., description="The microscope settings"),
    #         strategy: str = Field(..., description="The strategy elaborated by the Strategy Agent"),
    # ) -> SoftwareAgentOutput:
    #     """
    #     Calls the SoftwareAgent to generate code.
    #     Return a json object with 'intent' (code) and 'message'
    #     """
    #     # # Get current data dict
    #     data_dict = {
    #         "user_query": user_query,
    #         "reformulated_query": reformulated_query,
    #         "context": context,
    #         "additional_information": additional_information,
    #         "microscope_settings": microscope_settings,
    #         "strategy": strategy
    #     }
    #
    #     code = software_agent.generate_code(data_dict)
    #
    #     return code

    @mcp.tool(
        name="execute_python_code",
        description="""
        This tool is part of the feedback loop of the Microscope Toolset. It executes a given Python code 
        string and returns its output or any errors. If not already elaborated, you need to form a strategy and the code
        to run. Be aware of the precise constraints that these parameters have.
        """
    )
    def execute_python_code(
            user_query: str = Field(..., description="The user original query"),
            strategy: str = Field(..., description="""
            The strategy elaborated by the Main Agent.
            Given:
                - The original user query
                - The context (e.g., prior knowledge from the database or environment)
                - The microscope settings   
            
            
            Your main responsibility is to break the user's query into logical, sequenced steps, using available functions if possible.
            
            Build response
                - Based on the information, elaborate a strategy to answer the user query.
                - Break the query into smaller, logically ordered sub-tasks (if applicable).
                - Propose a concise, step-by-step strategy to address the user query.
            Response Style
                - Maintain a **scientific, concise, and unambiguous** communication style. Avoid redundant or non-technical phrasing.
            """),
            code: str = Field(..., description="""
            The code to be executed generated by the Main Agent.
            Given:
                - The original user query
                - The context (e.g., prior knowledge from the database or environment)
                - The microscope settings
                - The strategy of the Strategy Agent
            
            Your main responsibility is to generate Python code to answer the user's query using the strategy and all the available context information. Return raw text, don't format as markdown.
            
            Responsibilities
                - Use the strategy and the context to generate code that is:
                    - **Safe**: no security or hardware risks for the device or microscope.
                    - **Logical**: appropriate and functional.
                    - **Clear & Maintainable **: readable, cleanly structured.
                    - **Optimized**: efficient, minimal, and focused.
            
            Constrains
                - Use mmc (an instance of CMMCorePlus) to interact with the microscope.
                - Do **not** re-instantiate or reconfigure CMMCorePlus.
                - Only import essential, safe libraries.
                - **Avoid redundant narration** — just return the code in triple backticks.
                - **Print each result**, and if a value is None, print a human-readable message.
                - Include **minimal but meaningful comments** when needed.
                - We are using a GUI called napari-micromanager that is able to get a reference of the mmc object that you are using. Every images that you will produce will be shown in the GUI directly.
            """)
    ) -> dict[str, Any]:
        """
        Prepares and executes Python code using the Execute agent.
        Returns a dictionary with 'output' (the execution result) and 'error' (if any).
        """
        #code_string = code
        try:
            prepare_code_to_run = prepare_code(code)#code_string.strip("```")
            execution_output = executor.run_code(prepare_code_to_run)
            if "Error" in execution_output:
                return {
                    "user_query": user_query,
                    "strategy": strategy,
                    "code": code,
                    "error": execution_output
                }
            else:
                return {
                    "user_query": user_query,
                    "strategy": strategy,
                    "code": code,
                    "is_final_output": True,
                    "output": execution_output
                }
        except Exception as e:
            return {
                "user_query": user_query,
                "strategy": strategy,
                "code": code,
                "error": f"Code preparation/execution failed: {e}"
            }

    # @mcp.tool(
    #     name="save_result",
    #     description="This tool is part of the feedback loop of the Microscope Toolset. After showing the result to the user, "
    #                 "it will be asked to the user if the answer obtained was correct. We want to save into a database the "
    #                 "correct and the wrong answer to help you to answer the future user's questions. After you successfully "
    #                 "completed this, the user will likely ask you others questions or stop the server."
    # )
    # def save_result(
    #         user_query: str = Field(description="The user's response, typically 'correct' or 'wrong'.")
    # ):
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
    def show_result(
            user_query: str = Field(..., description="The user original query"),
            strategy: str = Field(..., description="The strategy elaborated by the Strategy Agent"),
            code: str = Field(..., description="The code to be executed generated by the SoftwareAgent"),
            error: str = Field(..., description="The error when running the code"),
            is_final_output: bool = Field(..., description="Whether the code was executed successfully"),
            output: str = Field(..., description="The output of the code"),
    ):
        """
        Shows the user the final output
        """
        # # Get current data dict
        # data_dict = microscope_session_object.get_data_dict()
        data_dict = {
            "user_query": user_query,
            "strategy": strategy,
            "code": code,
            "error": error,
            "is_final_output": is_final_output,
            "output": output
        }
        # show the final output
        if data_dict['is_final_output']:
            final_output = data_dict['output']
            return final_output
        else:
            message = "The final output was not reach yet!"
            return {
                is_final_output: False,
                message: message
            }


    return mcp


def run_server(mcp: FastMCP) -> None:
    """
    Start the MCP Microscope Toolset server.
    """
    mcp.run(transport="streamable-http")