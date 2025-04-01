from openai import OpenAI
from python.execute import Execute
from python.prepare_code import prepare_code


class SoftwareEngeneeringAgent:

    def __init__(self, client_openai: OpenAI):
        self.client_openai = client_openai

    def write_script(self, prompt: str, query: str) -> str:
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

    def run_code(self, prompt: str, query: str, executor: Execute):
        # format generated code
        code_generated = self.write_script(prompt=prompt, query=query)

        prepare_code_to_run = prepare_code(code_generated)

        # run the code
        output = executor.run_code(prepare_code_to_run)
        is_valid = False
        if "Error" not in output:
            is_valid = True
            return output, is_valid

        # an error occured
        error_prompt = output

        return error_prompt, is_valid
