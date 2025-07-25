from openai import OpenAI
from prompts.mainAgentPrompt import ANSWER_PROMPT


class NoCodingAgent:

    def __init__(self, client_openai: OpenAI):
        self.client_openai = client_openai

    def no_coding_answer(self, context):
        prompt = ANSWER_PROMPT

        response = self.client_openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": context["user_query"]
                }
            ]
        )

        return response.choices[0].message.content
