# This class reformulate the user query
import chromadb
from agents.agent import Agent

class MainAgent(Agent):

    def __init__(self, client_openai):
        super().__init__(client_openai)

    def reformulate_user_query(self, query: str) -> str:

        # create prompt
        # TODO Add the missing prompt
        prompt = ("""Prompt to add""")
        response = self.client_openai.chat.completions.create(
            model="gpt-4o-mini",
            messages= [
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": query.strip()
                }
            ]
        )

        return response.choices[0].message