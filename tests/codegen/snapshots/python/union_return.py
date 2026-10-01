from typing_extensions import TypedDict

class OperationNameResultGetPersonOrAnimalPerson(TypedDict):
    # typename: Person
    name: str
    age: int

class OperationNameResult(TypedDict):
    get_person_or_animal: OperationNameResultGetPersonOrAnimalPerson
