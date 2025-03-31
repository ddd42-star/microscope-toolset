from agents.main_agent import MainAgent
from agents.database_agent import DatabaseAgent
from agents.prompt_agent import PromptAgent
from agents.software_agent import SoftwareEngeneeringAgent
from agents.reasoning_agent import ReasoningAgent
from src.python.execute import Execute

def chat(
        mainAgent: MainAgent, 
        dbAgent: DatabaseAgent, 
        promptAgent: PromptAgent, 
        codeAgent: SoftwareEngeneeringAgent, 
        reacAgent: ReasoningAgent, 
        executor: Execute):

    choice = ""
    while choice != "quit":

        choice = input("Digit your question here: ").strip()

        # Reformulate the query
        reformulated_query = mainAgent.reformulate_user_query(choice)

        # Search into the database for the context
        context = dbAgent.search_into_database(refactored_query=reformulated_query)

        # create the prompt to send for the softwareengeering
        prompt_to_use = promptAgent.create_prompt(reformulated_query=reformulated_query, context=context)

        output, is_error = codeAgent.run_code(prompt=prompt_to_use, query=choice, executor=executor)

        # if code is not valid send it to the reasoning agent
        if not is_error:

            #new_strategy = ask_for_strategies_reasoning_agent(dbAgent,reacAgent, error=output, current_prompt=prompt_to_use, query=choice) # add "Your previous strategy didn't works. Try again."

            output = try_new_strategy(
                promptAgent=promptAgent, 
                codeAgent=codeAgent, 
                dbAgent=dbAgent, 
                reacAgent=reacAgent, 
                error=output, 
                current_prompt=prompt_to_use, 
                query=choice, 
                reformulated_query= reformulated_query, 
                context=context, 
                executor=executor)

        # otherwise, code has run successfully. Prepare the outpur for the user and add callback.
        # update the status of the microscope and wait for other messages
        
        # update the status of the microscope
        # TODO
        # refactor the output for the user
        # TODO


    return choice


def ask_for_strategies_reasoning_agent(dbAgent: DatabaseAgent, reacAgent: ReasoningAgent, error: str, current_prompt: str, query: str):

    
    # ask 3 strategies
    new_strategies = reacAgent.ask_for_reasoning(error=error, current_prompt=current_prompt, query=query)

    # Ask Database Agent if the strategies have 'real' functions and not just invented code
    new_strategy, ask_again = dbAgent.verify_strategies(new_strategies)

    if ask_again is False:
        return ask_for_strategies_reasoning_agent(dbAgent, reacAgent, error, current_prompt, query)
    
    
    return new_strategy


def try_new_strategy(
        promptAgent: PromptAgent, 
        codeAgent: SoftwareEngeneeringAgent,
        dbAgent: DatabaseAgent, 
        reacAgent: ReasoningAgent,
        error: str, 
        current_prompt: str, 
        query: str, 
        reformulated_query: str, 
        context: str, 
        executor: Execute):

    new_strategy = ask_for_strategies_reasoning_agent(dbAgent=dbAgent,reacAgent=reacAgent, error=error, current_prompt=current_prompt, query=query) # add "Your previous strategy didn't works. Try again."
    
    # create the prompt to send for the softwareengeering
    new_prompt_to_use = promptAgent.add_new_strategy(reformulated_query=reformulated_query, context=context, new_strategy=new_strategy)

    output, is_error = codeAgent.run_code(prompt=new_prompt_to_use, query=query, executor=executor)

    if not is_error:
        return try_new_strategy(
            promptAgent=promptAgent, 
            codeAgent=codeAgent, 
            dbAgent=dbAgent, 
            reacAgent=reacAgent, 
            error=error, 
            current_prompt= new_prompt_to_use, 
            query=query, 
            reformulated_query= reformulated_query, 
            context=context, 
            executor=executor)


    return output 


        