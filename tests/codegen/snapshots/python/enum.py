from typing_extensions import TypedDict
from enum import Enum

class Color(Enum):
    RED = "RED"
    GREEN = "GREEN"
    BLUE = "BLUE"

class OperationNameResult(TypedDict):
    enum: Color
