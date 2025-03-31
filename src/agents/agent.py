# abstra class for agent
from abc import ABC
from openai import OpenAI


class Agent(ABC):
    

    def __init__(self, client_openai: OpenAI) -> None:
        self.client_openai = client_openai

