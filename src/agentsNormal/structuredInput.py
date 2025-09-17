from pydantic import BaseModel, Field, RootModel
from typing import Dict, Any


class WrapUserRequest(BaseModel):

    intent: str
    parameters: list
    explanation: str

class ChainOfAction(BaseModel):

    action: str
    parameters: dict
    explanation: str

class PlannerRequest(BaseModel):

    steps: list[ChainOfAction]

class MicroscopeSettings(RootModel[Dict[str, Any]]):
    #properties: dict
    #current_status: dict
    #configuration_settings: dict
    """Microscope settings with arbitrary keys and values"""
    pass

class ApiInformation(BaseModel):
    type: str
    name: str
    signature: str
    description: str
    filename: str
    contextualize_text: str
    score: float

class MicroManagerInformation(BaseModel):
    doc_id: str
    content: str
    chunk_id: str
    filename: str
    score: float

class PdfInformation(BaseModel):
    content: str
    chunk_id: str
    filename: str
    score: float


