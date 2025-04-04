from openai import OpenAI
from python.execute import Execute
from python.prepare_code import prepare_code
from prompts.softwareEngineeringPrompt import SOFTWARE_PROMPT

class SoftwareEngeneeringAgent:

    def __init__(self, client_openai: OpenAI):
        self.client_openai = client_openai

    def write_script(self, fileName: str, context: str, microscope_status: str, previous_outputs: str, additional_infos: str, new_strategy: str, query: str) -> str:

        if len(context) == 0:
            context = "no information"

        prompt = SOFTWARE_PROMPT.format(filename=fileName,context=context, microscope_status=microscope_status, previous_outputs=previous_outputs, extra_infos=additional_infos,new_strategy=new_strategy)

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

    def run_code(self, fileName: str, context: str, microscope_status: str, previous_outputs: str, additional_infos: str, new_strategy: str, query: str, executor: Execute):
        # format generated code
        code_generated = self.write_script(fileName=fileName, context=context, microscope_status=microscope_status, previous_outputs=previous_outputs, additional_infos= additional_infos, new_strategy=new_strategy, query=query)

        #if code_generated == "Sorry, this question doesn't need Python code for the answer.": # stop if it doesn't need a script
        #    return code_generated, "", True
        print("generated code", code_generated)
        prepare_code_to_run = prepare_code(code_generated.strip("```"))
        print("prepare code: ", prepare_code_to_run)
        # run the code
        output = executor.run_code(prepare_code_to_run)
        is_valid = False
        if "Error" not in output:
            is_valid = True
            return output, prepare_code_to_run, is_valid

        # an error occured
        error_prompt = output

        return error_prompt, prepare_code_to_run, is_valid
