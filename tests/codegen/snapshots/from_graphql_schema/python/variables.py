from typing import List, Optional

class OperationNameResult:
    withInputs: bool

class PersonInput:
    name: str
    age: int

class ExampleInput:
    id: str
    name: str
    age: int
    person: PersonInput
    people: PersonInput
    optionalPeople: PersonInput

class OperationNameVariables:
    id: Optional[str]
    input: ExampleInput
    ids: List[str]
    ids2: Optional[List[Optional[str]]]
    ids3: Optional[List[Optional[List[Optional[str]]]]]
