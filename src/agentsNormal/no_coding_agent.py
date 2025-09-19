import json

from openai import OpenAI
from src.prompts.mainAgentPrompt import ANSWER_PROMPT
from src.agentsNormal.structuredOutput import NoCodingAgentOutput


class NoCodingAgent:

    def __init__(self, client_openai: OpenAI):
        self.client_openai = client_openai

    def no_coding_answer(self, context):
        prompt = ANSWER_PROMPT.format(additional_data=context)

        history = [
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": context["user_query"]
                }
            ]
        # response = self.client_openai.chat.completions.create(
        #     model="gpt-4.1-mini",
        #     messages=[
        #         {
        #             "role": "system",
        #             "content": prompt
        #         },
        #         {
        #             "role": "user",
        #             "content": context["user_query"]
        #         }
        #     ]
        # )
        response = self.client_openai.responses.parse(
            model="gpt-4.1-mini",
            input=history,
            text_format=NoCodingAgentOutput
        )

        parsed_response = json.loads(response.output_text)

        return parsed_response

        return response.choices[0].message.content
