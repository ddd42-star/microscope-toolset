from pydantic import BaseModel, Field



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

class ClassificationAgentOutput(BaseModel):

    intent: str
    message: str

class RephraseOutput(BaseModel):

    intent: str
    message: str

class ExtractKeywordOutput(BaseModel):
    intent: str
    message: str