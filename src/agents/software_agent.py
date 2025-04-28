from openai import OpenAI
from python.execute import Execute
from python.prepare_code import prepare_code
from prompts.softwareEngineeringPrompt import SOFTWARE_PROMPT, SOFTWARE_AGENT, SOFTWARE_AGENT_RETRY
from agents.structuredOutput import SoftwareAgentOutput
import ast
import logging


class SoftwareEngeneeringAgent:

    def __init__(self, client_openai: OpenAI):
        self.client_openai = client_openai

    def write_script(self, fileName: str, context: str, microscope_status: str, previous_outputs: str,
                     conversation: str, new_strategy: str, query: str, query_strategy) -> str:
        logger = logging.getLogger(__name__)

        if len(microscope_status) == 0:
            microscope_status = "no information"

        if len(previous_outputs) == 0:
            previous_outputs = "no information"
        if len(conversation) == 0:
            previous_outputs = "no information"
        if len(new_strategy) == 0:
            new_strategy = "no information"


        prompt = SOFTWARE_PROMPT.format(filename=fileName, context=context, microscope_status=microscope_status,
                                        previous_outputs=previous_outputs, conversation=conversation,
                                        new_strategy=new_strategy, query_strategy=query_strategy)
        logger.info("Software prompt: %s", prompt)
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

    def run_code(self, fileName: str, context: str, microscope_status: str, previous_outputs: str,
                 conversation: str, new_strategy: str, query: str, query_strategy: str, executor: Execute):
        logger = logging.getLogger(__name__)
        # format generated code
        code_generated = self.write_script(fileName=fileName, context=context, microscope_status=microscope_status,
                                           previous_outputs=previous_outputs, conversation=conversation,
                                           new_strategy=new_strategy, query=query, query_strategy= query_strategy)

        # if code_generated == "Sorry, this question doesn't need Python code for the answer.": # stop if it doesn't need a script
        #    return code_generated, "", True
        # print("generated code", code_generated)
        logger.info("generated code: %s", code_generated)
        prepare_code_to_run = prepare_code(code_generated.strip("```"))
        # print("prepare code: ", prepare_code_to_run)
        logger.info("prepare code: %s", prepare_code_to_run)
        # run the code
        output = executor.run_code(prepare_code_to_run)
        is_valid = False
        if "Error" not in output:
            is_valid = True
            return output, prepare_code_to_run, is_valid

        # an error occurred
        error_prompt = output

        return error_prompt, prepare_code_to_run, is_valid

    def generate_code(self, context):

        prompt = SOFTWARE_AGENT.format(
            conversation=context["conversation"] or "no information",
            context=context["context"] or "no information",
            microscope_status = context["microscope_status"] or "no information",
            previous_outputs = context["previous_outputs"] or "no information",
            query_strategy=context["main_agent_strategy"] or "no information"
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
                "name": "SoftwareAgentOutput",
                "description": "Parser of the JSON object.",
                "parameters": SoftwareAgentOutput.model_json_schema()
            }],
            function_call="auto"
            )

        return self.parse_agent_response(response.choices[0].message.content)

    def fix_code(self, context):

        prompt = SOFTWARE_AGENT_RETRY.format(
            conversation=context["conversation"] or "no information",
            context=context["context"] or "no information",
            microscope_status=context["microscope_status"] or "no information",
            previous_outputs=context["previous_outputs"] or "no information",
            query_strategy=context["main_agent_strategy"] or "no information",
            error_message=context["error"] or "no information",
            error_analysis=context["error_analysis"] or "no information",
            new_strategy=context["new_strategy"] or "no information"
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
                "name": "SoftwareAgentOutput",
                "description": "Parser of the JSON object.",
                "parameters": SoftwareAgentOutput.model_json_schema()
            }],
            function_call="auto"
        )

        return self.parse_agent_response(response.choices[0].message.content)

    def parse_agent_response(self, response: str):
        # try:
        #     return ast.literal_eval(response)
        # except (ValueError, SyntaxError):
        #     pass
        # verify if the LLM managed to output
        # TODO: add refusal check in the output
        output_raw = SoftwareAgentOutput.model_validate_json(response)

        print(output_raw)
        print(output_raw.intent)
        print(output_raw.message)

        return output_raw