from typing import List, Optional

class OperationNameResult:
    with_inputs: bool

class PersonInput:
    name: str
    age: Optional[int] = None

class ExampleInput:
    id: str
    name: str
    age: int
    person: Optional[PersonInput]
    people: List[PersonInput]
    optional_people: Optional[List[PersonInput]]

class OperationNameVariables:
    id: Optional[str]
    input: ExampleInput
    ids: List[str]
    ids2: Optional[List[Optional[str]]]
    ids3: Optional[List[Optional[List[Optional[str]]]]]
