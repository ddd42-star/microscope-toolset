from pydantic import BaseModel, Field



class MainAgentOutput(BaseModel):

    intent: str
    message: str




