from typing import List, Optional

class OperationNameResultOptionalListOfPeople:
    name: str
    age: int

class OperationNameResult:
    optional_list_of_people: Optional[list[OperationNameResultOptionalListOfPeople]]
