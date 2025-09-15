import json
from openai import OpenAI

class BaseAgent:

    def __init__(self, client_openai: OpenAI):
        self.client_openai = client_openai


    def call_agent(self, model: str, input_user: list, error_string: str, output_format):
        """
        This function declare how the agent is called
        """
        try:
            response = self.client_openai.responses.parse(
                model=model,
                input=input_user,
                text_format=output_format
            )

            # parse json object
            parsed_response = json.loads(response.output_text)

            return parsed_response
        except Exception as e:
            return {"intent": "error", "message": f"{error_string}: {e}"}
