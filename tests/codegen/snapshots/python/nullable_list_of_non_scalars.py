from typing_extensions import TypedDict
from typing import List, Optional

class OperationNameResultOptionalListOfPeople(TypedDict):
    name: str
    age: int

class OperationNameResult(TypedDict):
    optional_list_of_people: Optional[list[OperationNameResultOptionalListOfPeople]]
