from agents.agent import Agent

class DatabaseAgent(Agent):

    def __init__(self, client_openai):
        super().__init__(client_openai)

    