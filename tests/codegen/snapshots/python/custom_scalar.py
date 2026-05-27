from typing_extensions import TypedDict
from typing import NewType

JSON = NewType("JSON", str)

class OperationNameResult(TypedDict):
    json: JSON
