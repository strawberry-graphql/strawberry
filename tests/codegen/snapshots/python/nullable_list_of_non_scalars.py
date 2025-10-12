from typing import List

class OperationNameResultOptionalListOfPeople:
    name: str
    age: int

class OperationNameResult:
    optional_list_of_people: list[OperationNameResultOptionalListOfPeople] | None
