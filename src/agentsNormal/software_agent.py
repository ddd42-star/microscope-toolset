from openai import OpenAI
from prompts.softwareEngineeringPrompt import SOFTWARE_AGENT, SOFTWARE_AGENT_RETRY
from agentsNormal.structuredOutput import SoftwareAgentOutput


class SoftwareEngeneeringAgent:

    def __init__(self, client_openai: OpenAI):
        self.client_openai = client_openai

    def generate_code(self, context):

        prompt = SOFTWARE_AGENT.format(
            context=context["context"] or "no information",
            microscope_status = context["microscope_status"] or "no information",
            previous_outputs = context["previous_outputs"] or "no information"
        )
        #print(prompt)
        history = [{"role": "system", "content": prompt}, {"role": "user", "content": context["user_query"]}] + context["conversation"]
        response = self.client_openai.beta.chat.completions.parse(
            model="gpt-4.1-mini",
            messages=history,
            response_format=SoftwareAgentOutput
            )

        return self.parse_agent_response(response.choices[0].message.content)

    def fix_code(self, context):

        prompt = SOFTWARE_AGENT_RETRY.format(
            context=context["context"] or "no information",
            microscope_status=context["microscope_status"] or "no information",
            previous_outputs=context["previous_outputs"] or "no information"
        )
        history = [{"role": "system", "content": prompt}, {"role": "user", "content": context["user_query"]}] + context["conversation"]
        response = self.client_openai.beta.chat.completions.parse(
            model="gpt-4.1-mini",
            messages=history,
            response_format=SoftwareAgentOutput
        )

        return self.parse_agent_response(response.choices[0].message.content)

    def parse_agent_response(self, response: str):
        # try:
        #     return ast.literal_eval(response)
        # except (ValueError, SyntaxError):
        #     pass
        # verify if the LLM managed to output
        # TODO: add refusal check in the output
        #print(response)
        output_raw = SoftwareAgentOutput.model_validate_json(response)

        #print(output_raw)
        #print(output_raw.intent)
        #print(output_raw.message)

        return output_raw