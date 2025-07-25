from openai import OpenAI
from prompts.mainAgentPrompt import CLASSIFY_INTENT
from agentsNormal.structuredOutput import ClassificationAgentOutput

class ClassifyAgent:

    def __init__(self, client_openai: OpenAI):
        self.client_openai = client_openai

    def classify_user_intent(self, context):

        prompt = CLASSIFY_INTENT.format(
            context=context['context'] or "no information",
            microscope_status=context['microscope_status'] or "no information",
            previous_outputs=context['previous_outputs'] or "no information"
        )

        history = [{"role": "system", "content": prompt},
                   {"role": "user", "content": context['user_query']}] + context['conversation']

        try:
            response = self.client_openai.beta.chat.completions.parse(
                model="gpt-4.1-mini",
                messages=history,
                response_format=ClassificationAgentOutput
            )
            # parse response
            parsed_response = self.parse_agent_response(response.choices[0].message.content)
            return parsed_response
        except Exception as e:
            return {"intent": "error", "message": f"Failed to classify intent: {e}"}

    def parse_agent_response(self,response: str):

        try:
            return ClassificationAgentOutput.model_validate_json(response)
        except Exception as e:
            return e