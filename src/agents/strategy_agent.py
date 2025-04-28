from openai import OpenAI
from prompts.strategyAgentPrompt import STRATEGY
from agents.structuredOutput import StrategyAgentOutput
import ast

class StrategyAgent:

    def __init__(self, client_openai: OpenAI):

        self.client_openai = client_openai


    def generate_strategy(self, context):

        prompt = STRATEGY.format(
            conversation=context["conversation"] or "no information",
            context=context["context"] or "no information",
            microscope_status=context["microscope_status"] or "no information",
            previous_outputs=context["previous_outputs"] or "no information",
            extra_infos=context["extra_infos"] or "no information"
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
                    "content": context["user_query"]
                }
            ],
            functions=[{
                "name": "StrategyAgentOutput",
                "description": "Parser of the JSON object.",
                "parameters": StrategyAgentOutput.model_json_schema()
            }],
            function_call="auto"
        )

        return self.parse_agent_response(response.choices[0].message.content)  # it should be a python dictonary

    def parse_agent_response(self, response: str):
        # try:
        #     return ast.literal_eval(response)
        # except (ValueError, SyntaxError):
        #     pass
        # verify if the LLM managed to output
        # TODO: add refusal check in the output
        output_raw = StrategyAgentOutput.model_validate_json(response)

        print(output_raw)
        print(output_raw.intent)
        print(output_raw.message)

        return output_raw

    def revise_strategy(self, context):

        prompt = STRATEGY.format(
            conversation=context["conversation"] or "no information",
            context=context["context"] or "no information",
            microscope_status=context["microscope_status"] or "no information",
            previous_outputs=context["previous_outputs"] or "no information",
            extra_infos=context["extra_infos"] or "no information"
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
                    "content": context["user_query"]
                }
            ]
        )

        return self.parse_agent_response(response.choices[0].message.content)  # it should be a python dictonary



