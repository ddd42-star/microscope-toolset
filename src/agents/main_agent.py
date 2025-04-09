# This class reformulate the user query
import chromadb
from openai import OpenAI
from prompts.mainAgentPrompt import  MAIN_PROMPT, ANSWER_PROMPT, REASONING_MAIN
from typing import Optional
import logging


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


    def evaluate_query(self, query: str, microscope_status: str, previous_outputs: str, context: str, additional_infos: str, conversation: str):

        logger = logging.getLogger(__name__)
        if len(microscope_status) == 0:
            microscope_status = "no information"

        if len(previous_outputs) == 0:
            previous_outputs = "no information"
        if len(additional_infos) == 0:
            additional_infos = "no information"
        if len(conversation) == 0:
            conversation = "no information"

        #prompt = MAIN_PROMPT.format(context=context, microscope_status=microscope_status, previous_outputs = previous_outputs, extra_infos=additional_infos)
        prompt = REASONING_MAIN.format(conversation=conversation, context=context, microscope_status=microscope_status, previous_outputs = previous_outputs, extra_infos=additional_infos)
        #print(prompt)
        logger.info("main agent prompt: %s", prompt)
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

    def main_agent(self, query: str, microscope_status: str, previous_outputs: str, context: str, conversation: str) -> str:
        logger = logging.getLogger(__name__)
        if len(microscope_status) == 0:
            microscope_status = "no information"

        if len(previous_outputs) == 0:
            previous_outputs = "no information"
        if len(conversation) == 0:
            previous_outputs = "no information"

        prompt = ANSWER_PROMPT.format(conversation=conversation, context=context, microscope_status=microscope_status,
                                    previous_outputs=previous_outputs)
        #print(prompt)
        logger.info("main agent prompt: %s", prompt)
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

