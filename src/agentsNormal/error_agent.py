from openai import OpenAI
from src.prompts.errorAgentprompt import ERROR_ANALYSIS
from src.agentsNormal.structuredOutput import ErrorAgentOutput

class ErrorAgent:

    def __init__(self, client_openai: OpenAI):

        self.client_openai = client_openai


    def analyze_error(self, context):

        prompt = ERROR_ANALYSIS.format(
            context=context["context"] or "no information",
            microscope_status=context["microscope_status"] or "no information",
            previous_outputs=context["previous_outputs"] or "no information"
        )
        history = [{"role": "system", "content": prompt}, {"role": "user", "content": context["user_query"]}] + context[
            "conversation"]
        response = self.client_openai.beta.chat.completions.parse(
            model="gpt-4.1-mini",
            messages=history,
            response_format=ErrorAgentOutput
        )

        return self.parse_agent_response(response.choices[0].message.content)  # it should be a local dictonary

    def parse_agent_response(self, response: str):
        # try:
        #     return ast.literal_eval(response)
        # except (ValueError, SyntaxError):
        #     pass
        # verify if the LLM managed to output
        # TODO: add refusal check in the output
        output_raw = ErrorAgentOutput.model_validate_json(response)

        #print(output_raw)
        #print(output_raw.intent)
        #print(output_raw.message)

        return output_raw