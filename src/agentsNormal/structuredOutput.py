from pydantic import BaseModel, Field



class MainAgentOutput(BaseModel):

    intent: str
    message: str

class StrategyAgentOutput(BaseModel):

    intent: str
    message: str


class SoftwareAgentOutput(BaseModel):

    intent: str
    message: str

class ErrorAgentOutput(BaseModel):

    intent: str
    message: str

class LoggerAgentOutput(BaseModel):

    intent: str
    message: str

