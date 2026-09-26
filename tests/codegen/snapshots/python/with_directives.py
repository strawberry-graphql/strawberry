from typing_extensions import TypedDict

class OperationNameResultPerson(TypedDict):
    name: str

class OperationNameResult(TypedDict):
    person: OperationNameResultPerson
