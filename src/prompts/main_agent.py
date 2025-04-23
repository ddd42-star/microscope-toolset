from agents.database_agent import DatabaseAgent
from agents.software_agent import SoftwareEngeneeringAgent
from agents.reasoning_agent import ReasoningAgent
from openai import OpenAI

class MainAgentState:

    def __init__(self, client_openai: OpenAI, db_agent: DatabaseAgent, software_agent: SoftwareEngeneeringAgent, reasoning_agent: ReasoningAgent):
        self.state = "initial"
        self.context = {
            "conversation": [],
            "user_query": "",
            "context": "",
            "extra_infos": "",
            "microscope_status":{},
            "previous_outputs": "",
            "main_agent_strategy": None,
            "new_strategy": None,
            "code": None,
            "error": None

        }
        self.client_openai = client_openai
        self.db_agent = db_agent
        self.software_agent = software_agent
        self.reasoning_agent = reasoning_agent

        # add differents agents

    def process_query(self, user_query: str):

        if user_query == "quit":
            return "quit"

        else:
            # return state, {dict with information}
            if self.state == "initial":
                # retrieve the context from the vector db
                # retrieve the log from the feedback db
                context = self.db_agent.look_for_context(query=user_query)
                self.context["context"] = context
                self.state = "planning_strategy"

                return "planning_strategy", { "user_query": user_query}
            elif self.state == "awaiting_clarification":
                # 1) awaiting clarification from user query
                # 2) awaiting clarification from agent strategy
                pass
            elif self.state == "planning_strategy":
                # create a strategy

                pass
            elif self.state == "awaiting_user_approval":
                pass
            elif self.state == "validating_strategy":
                pass
            elif self.state == "executing_code":
                pass
            elif self.state == "handling_errors":
                pass
            elif self.state == "finish":
                pass

        return None

