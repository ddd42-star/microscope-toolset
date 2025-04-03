# This class reformulate the user query
import chromadb
from openai import OpenAI
from prompts.mainAgentPrompt import  MAIN_PROMPT
from typing import Optional


class MainAgent:

    def __init__(self, client_openai: OpenAI):
        self.client_openai = client_openai

    def reformulate_user_query(self, query: str, microscope_status: str, previous_outputs: str) -> str:
        if len(microscope_status) == 0:
            microscope_status = "no information"

        if len(previous_outputs) == 0:
            previous_outputs = "no information"

        prompt = MAIN_PROMPT.format(microscope_status=microscope_status, previous_outputs = previous_outputs)
        response = self.client_openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": query.strip()
                },
            ],
        )

        return response.choices[0].message.content
