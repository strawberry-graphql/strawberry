from typing_extensions import TypedDict
from typing import List

class OperationNameResultPerson(TypedDict):
    name: str

class OperationNameResultListOfPeople(TypedDict):
    name: str

class OperationNameResult(TypedDict):
    person: OperationNameResultPerson
    list_of_people: list[OperationNameResultListOfPeople]
