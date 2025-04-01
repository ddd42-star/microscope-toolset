# This class reformulate the user query
import chromadb
from openai import OpenAI


class MainAgent:

    def __init__(self, client_openai: OpenAI):
        self.client_openai = client_openai

    def reformulate_user_query(self, query: str) -> str:
        # create prompt
        # TODO Add the missing prompt
        prompt = ("""Prompt to add""")
        response = self.client_openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
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
