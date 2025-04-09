import sys
import time

from agents.main_agent import MainAgent
from agents.database_agent import DatabaseAgent
from agents.prompt_agent import PromptAgent
from agents.software_agent import SoftwareEngeneeringAgent
from agents.reasoning_agent import ReasoningAgent
from python.execute import Execute
from microscope.microscope_status import MicroscopeStatus
import logging


def chat(
        mainAgent: MainAgent,
        dbAgent: DatabaseAgent,
        promptAgent: PromptAgent,
        codeAgent: SoftwareEngeneeringAgent,
        reacAgent: ReasoningAgent,
        executor: Execute,
        microscopeStatus: MicroscopeStatus,
        fileName: str):
    chatLogger = logging.getLogger(__name__)
    microscope_status = ""
    output = ""
    additional_infos = ""
    conversation = ""
    evaluate_query = ""
    while True:
        choice = input("Digit your question here: ").strip()

        if choice == "quit":
            break
        conversation += choice

        # Reformulate the query
        # reformulated_query = mainAgent.reformulate_user_query(choice, microscope_status, output)
        # print("reformulated question: ", reformulated_query)
        # Search into the database for the context
        # context = dbAgent.search_into_database(refactored_query=reformulated_query)
        context = dbAgent.look_for_context(query=choice)  # choose raw query for searching the in the database
        # print("context", context)

        # Let main Agent decide if the answer can be answered with a script or not
        user_input = ""
        while user_input != "yes":
            # first evaluate the user query
            evaluate_query = mainAgent.evaluate_query(query=choice, microscope_status=microscope_status,
                                                      previous_outputs=output, context=context,
                                                      additional_infos=additional_infos, conversation=conversation)

            chatLogger.info("evaluate query: %s", evaluate_query)

            if "I need more information" in evaluate_query:
                additional_infos_user = input("Add additional information here: ").strip()
                additional_infos = "LLM: " + evaluate_query + "\n" + "USER: " + additional_infos_user
                # update conversation
                conversation += "\n" + additional_infos
            elif "This is my strategy" in evaluate_query:
                user_input = input("user: ").lower().strip() # not really a strong implementations since it depends on the user a lot
                additional_infos = "LLM: " + evaluate_query + "\n" + "USER: " + user_input
                conversation += "\n" + additional_infos


        # while "I need more information" in evaluate_query:
        #     additional_infos_user = input("Add additional information here: ").strip()
        #     additional_infos = "LLM: " + evaluate_query + "\n" + "USER added: " + additional_infos_user
        #     # update conversation
        #     conversation += "\n" + additional_infos
        #     evaluate_query = mainAgent.evaluate_query(query=choice, microscope_status=microscope_status,
        #                                               previous_outputs=evaluate_query, context=context,
        #                                               additional_infos=additional_infos, conversation= conversation)
        #     chatLogger.info("evaluate query: %s", evaluate_query)
        # verify that the user confirmed a strategy

        # now decide where to send the strategy
        if "This query does not require Python code." in evaluate_query:
            output = mainAgent.main_agent(query=choice, microscope_status=microscope_status, previous_outputs=output,
                                          context=context, conversation=conversation)
        elif "This is my strategy" in evaluate_query:
            # create the prompt to send for the softwareengeering
            # prompt_to_use = promptAgent.create_prompt(reformulated_query=reformulated_query, context=context)

            output, code, is_error = codeAgent.run_code(fileName=fileName, context=context,
                                                        microscope_status=microscope_status, previous_outputs=output,
                                                        conversation=conversation, new_strategy="",
                                                        query=choice, query_strategy=evaluate_query, executor=executor)
            # print("output: ", output)
            # print("code: ", code)
            # chatLogger.info(output)
            # chatLogger.info(code)
            # if code is not valid send it to the reasoning agent
            if not is_error:
                # new_strategy = ask_for_strategies_reasoning_agent(dbAgent,reacAgent, error=output, current_prompt=prompt_to_use, query=choice)
                # # add "Your previous strategy didn't works. Try again."

                output = try_new_strategy(
                    promptAgent=promptAgent,
                    codeAgent=codeAgent,
                    dbAgent=dbAgent,
                    reacAgent=reacAgent,
                    error=output,
                    microscope_status=microscope_status,
                    previous_output=output,
                    conversation=conversation,
                    code=code,
                    query=choice,
                    context=context,
                    executor=executor,
                    fileName=fileName,
                    query_strategy=evaluate_query)
            # update conversation
            conversation += "\n" + "LLM: " + output
            # otherwise, code has run successfully. Prepare the output for the user and add callback.
            # update the status of the microscope and wait for other messages

            # update the status of the microscope
            # if len(microscopeStatus.update()) == 0:
            #    microscope_status = microscope_status
            # else:
            #    microscope_status = "\n".join(microscopeStatus.update()) # new status
            # microscopeStatus.update() # new status
            # refactor the output for the user
        # print("###########################################")
        # print("OpenAI:")
        # print(output)
        # print("###########################################")
        chatLogger.info("""
        OpenAI:
        %s
        """, output)

    return choice


def ask_for_strategies_reasoning_agent(dbAgent: DatabaseAgent, reacAgent: ReasoningAgent, conversation: str, context: str,
                                       microscope_status: str, previous_outputs: str, code: str, error: str,
                                       query: str, query_strategy: str):
    logger = logging.getLogger(__name__)
    # ask 3 strategies
    new_strategies = reacAgent.ask_for_reasoning(conversation=conversation, context=context, microscope_status=microscope_status,
                                                 previous_outputs=previous_outputs, code=code, error=error, query=query, query_strategy=query_strategy)
    # print("strategies: ", new_strategies)
    logger.info(new_strategies)
    # stop if cannot fix th error
    if "Based on the current error I didn't found any strategy to fix the issue." in new_strategies:
        return new_strategies # stop it and go back asking a new questions
    # Ask Database Agent if the strategies have 'real' functions and not just invented code
    new_strategy, ask_again = dbAgent.verify_strategies(new_strategies)

    if ask_again is False:
        return ask_for_strategies_reasoning_agent(dbAgent, reacAgent, conversation, context, microscope_status, previous_outputs,
                                                  code, error, query, query_strategy)

    return new_strategy


def try_new_strategy(
        promptAgent: PromptAgent,
        codeAgent: SoftwareEngeneeringAgent,
        dbAgent: DatabaseAgent,
        reacAgent: ReasoningAgent,
        error: str,
        microscope_status: str,
        previous_output: str,
        conversation: str,
        code: str,
        query: str,
        query_strategy: str,
        context: str,
        executor: Execute,
        fileName: str):
    new_strategy = ask_for_strategies_reasoning_agent(dbAgent=dbAgent, reacAgent=reacAgent, conversation=conversation, context=context,
                                                      microscope_status=microscope_status,
                                                      previous_outputs=previous_output, code=code, error=error,
                                                      query=query, query_strategy=query_strategy)  # add "Your previous strategy didn't works. Try again."
    if "Based on the current error I didn't found any strategy to fix the issue." in new_strategy:
        return new_strategy # stop and go back asking the question
    # create the prompt to send for the softwareengeering
    # new_prompt_to_use = promptAgent.add_new_strategy(reformulated_query=reformulated_query, context=context, new_strategy=new_strategy)
    # update conversation
    conversation += "\n" + "LLM: " + error
    conversation += "\n" + "LLM: " + new_strategy

    output, code, is_error = codeAgent.run_code(fileName=fileName, context=context, microscope_status=microscope_status,
                                                previous_outputs=previous_output, conversation=conversation,
                                                new_strategy=new_strategy, query=query, query_strategy=query_strategy, executor=executor)
    conversation += "\n" + "LLM: " + output
    if not is_error:
        return try_new_strategy(
            promptAgent=promptAgent,
            codeAgent=codeAgent,
            dbAgent=dbAgent,
            reacAgent=reacAgent,
            error=error,
            microscope_status=microscope_status,
            previous_output=previous_output,
            conversation=conversation,
            code=code,
            query=query,
            query_strategy=query_strategy,
            context=context,
            executor=executor,
            fileName=fileName)

    return output
