from typing import NewType

JSON = NewType("JSON", str)

class OperationNameResult:
    json: JSON
