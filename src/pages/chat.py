from agents.main_agent import MainAgent
from agents.database_agent import DatabaseAgent
from agents.prompt_agent import PromptAgent
from agents.software_agent import SoftwareEngeneeringAgent
from agents.reasoning_agent import ReasoningAgent
from python.execute import Execute
from microscope.microscope_status import MicroscopeStatus

def chat(
        mainAgent: MainAgent, 
        dbAgent: DatabaseAgent, 
        promptAgent: PromptAgent, 
        codeAgent: SoftwareEngeneeringAgent, 
        reacAgent: ReasoningAgent, 
        executor: Execute,
        microscopeStatus: MicroscopeStatus,
        fileName: str):

    choice = ""
    microscope_status = ""
    output = ""
    while True:

        choice = input("Digit your question here: ").strip()

        if choice == "quit":
            break
        print("choice", choice)


        # Reformulate the query
        reformulated_query = mainAgent.reformulate_user_query(choice, microscope_status, output)
        print("reformulated question: ", reformulated_query)
        # Search into the database for the context
        context = dbAgent.search_into_database(refactored_query=reformulated_query)
        print("context", context)

        # create the prompt to send for the softwareengeering
        #prompt_to_use = promptAgent.create_prompt(reformulated_query=reformulated_query, context=context)

        output, code, is_error = codeAgent.run_code(fileName=fileName, context=context, microscope_status=microscope_status, previous_outputs=output, new_strategy="", query=choice, executor=executor)
        print("output: ", output)
        print("code: ", code)
        # if code is not valid send it to the reasoning agent
        if not is_error:

            #new_strategy = ask_for_strategies_reasoning_agent(dbAgent,reacAgent, error=output, current_prompt=prompt_to_use, query=choice) 
            # # add "Your previous strategy didn't works. Try again."

            output = try_new_strategy(
                promptAgent=promptAgent, 
                codeAgent=codeAgent, 
                dbAgent=dbAgent, 
                reacAgent=reacAgent, 
                error=output, 
                microscope_status=microscope_status,
                previous_output= output,
                code=code,
                query=choice, 
                reformulated_query= reformulated_query, 
                context=context, 
                executor=executor,
                fileName=fileName)

        # otherwise, code has run successfully. Prepare the output for the user and add callback.
        # update the status of the microscope and wait for other messages
        
        # update the status of the microscope
        #if len(microscopeStatus.update()) == 0:
        #    microscope_status = microscope_status
        #else:
        #    microscope_status = "\n".join(microscopeStatus.update()) # new status
        #microscopeStatus.update() # new status
        # refactor the output for the user
        print("###########################################")
        print("OpenAI:")
        print(output)
        print("###########################################")

    return choice


def ask_for_strategies_reasoning_agent(dbAgent: DatabaseAgent, reacAgent: ReasoningAgent, context: str, microscope_status: str, previous_outputs: str, code: str, error: str, query: str):

    
    # ask 3 strategies
    new_strategies = reacAgent.ask_for_reasoning(context=context, microscope_status=microscope_status, previous_outputs=previous_outputs, code=code, error=error, query=query)
    print("strategies: ", new_strategies)

    # Ask Database Agent if the strategies have 'real' functions and not just invented code
    new_strategy, ask_again = dbAgent.verify_strategies(new_strategies)

    if ask_again is False:
        return ask_for_strategies_reasoning_agent(dbAgent, reacAgent, context, microscope_status, previous_outputs, code, error, query)
    
    
    return new_strategy


def try_new_strategy(
        promptAgent: PromptAgent, 
        codeAgent: SoftwareEngeneeringAgent,
        dbAgent: DatabaseAgent, 
        reacAgent: ReasoningAgent,
        error: str, 
        microscope_status: str,
        previous_output: str,
        code: str,
        query: str, 
        reformulated_query: str, 
        context: str, 
        executor: Execute,
        fileName: str):

    new_strategy = ask_for_strategies_reasoning_agent(dbAgent=dbAgent,reacAgent=reacAgent, context=context, microscope_status=microscope_status, previous_outputs=previous_output, code=code, error=error, query=query) # add "Your previous strategy didn't works. Try again."
    
    # create the prompt to send for the softwareengeering
    #new_prompt_to_use = promptAgent.add_new_strategy(reformulated_query=reformulated_query, context=context, new_strategy=new_strategy)

    output, code, is_error = codeAgent.run_code(fileName=fileName, context=context, microscope_status=microscope_status, previous_outputs=previous_output, new_strategy=new_strategy, query=query, executor=executor)

    if not is_error:
        return try_new_strategy(
            promptAgent=promptAgent, 
            codeAgent=codeAgent, 
            dbAgent=dbAgent, 
            reacAgent=reacAgent, 
            error=error, 
            microscope_status=microscope_status,
            previous_output=previous_output,
            code=code,
            query=query, 
            reformulated_query= reformulated_query, 
            context=context, 
            executor=executor,
            fileName=fileName)


    return output 


        