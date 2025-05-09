from openai import OpenAI

class ClarificationAgent:

    def __init__(self, client_openai: OpenAI):

        self.client_openai = client_openai



    def user_clarification(self, context):

        user_answer = input("User: ")

        return user_answer
