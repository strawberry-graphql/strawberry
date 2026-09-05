from typing_extensions import TypedDict

class PersonName(TypedDict):
    # typename: Person
    name: str

class OperationNameResult(TypedDict):
    person: PersonName
