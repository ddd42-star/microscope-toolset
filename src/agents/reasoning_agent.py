from openai import OpenAI


class ReasoningAgent:

    def __init__(self, client_openai: OpenAI):
        self.client_openai = client_openai

    def ask_for_reasoning(self, error: str, current_prompt: str, query: str) -> str:
        # add part: "An error occured. Elaborate three reasoning"
        prompt = current_prompt + "\n" + error
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
