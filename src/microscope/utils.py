from pydantic import BaseModel
from typing import Any


class Property(BaseModel):
    default: Any
    enum: list = None
    maximum: float = None
    minimum: float = None
    preInit: bool = None
    readOnly: bool = None
    sequenceMaxLength: int = None
    sequenceable: bool = None
    type: str = None

class Properties(BaseModel):
    propertyName: str = None
    propertyValue: Property = None

class Device(BaseModel):
    title: str = None
    description: str = None
    properties: Properties = None
    type: str = None

class Devices(BaseModel):
    label: str = None
    device: Device = None




