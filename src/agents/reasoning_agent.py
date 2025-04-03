from openai import OpenAI
from prompts.reasoningAgentPrompt import REASONING_PROMPT

class ReasoningAgent:

    def __init__(self, client_openai: OpenAI):
        self.client_openai = client_openai

    def ask_for_reasoning(self, context: str, microscope_status: str, previous_outputs: str, code: str, error: str, query: str) -> str:
        # add part: "An error occurred. Elaborate three reasoning"
        prompt = REASONING_PROMPT.format(
            context=context,
            microscope_status=microscope_status,
            previous_outputs=previous_outputs,
            errors=error,
            code=code
        )
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
                },
            ],
        )

        return response.choices[0].message.content
