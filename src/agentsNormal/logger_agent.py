from openai import OpenAI
from src.prompts.loggerAgentPrompt import SUMMARY
from src.agentsNormal.structuredOutput import LoggerAgentOutput

class LoggerAgent:

    def __init__(self, client_openai: OpenAI):

        self.client_openai = client_openai

    def prepare_summary(self, context):

        prompt = SUMMARY
        task = "Create a summary of the interaction occurred between one user and the multi-agent system."
        history = [{"role": "system", "content": prompt}, {"role": "user", "content": task}] + context[
            "conversation"]
        response = self.client_openai.beta.chat.completions.parse(
            model="gpt-4.1-mini",
            messages=history,
            response_format=LoggerAgentOutput
        )

        return self.parse_response(response.choices[0].message.content)


    def parse_response(self, response: str):

        output_raw = LoggerAgentOutput.model_validate_json(response)
        print(output_raw)

        return  output_raw
