from agents.main_agent import MainAgent
from agents.database_agent import DatabaseAgent
from agents.prompt_agent import PromptAgent
from agents.software_agent import SoftwareEngeneeringAgent
from agents.reasoning_agent import ReasoningAgent

def chat(mainAgent: MainAgent, dbAgent: DatabaseAgent, promptAgent: PromptAgent, codeAgend: SoftwareEngeneeringAgent, reacAgent: ReasoningAgent):

    choice = ""
    while choice != "quit":

        choice = input("Digit your question here: ").strip()

        # Reformulate the query
        reformulated_query = mainAgent.reformulate_user_query(choice)

        # Search into the database for the context
        context = dbAgent.search_into_database(refactored_query=reformulated_query)




    return choice