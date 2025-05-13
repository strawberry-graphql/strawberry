from typing import List

class OperationNameResultPerson:
    name: str

class OperationNameResultListOfPeople:
    name: str

class OperationNameResult:
    person: OperationNameResultPerson
    list_of_people: list[OperationNameResultListOfPeople]
