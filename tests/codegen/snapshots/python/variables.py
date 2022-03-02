from typing import List, Optional

class OperationNameResult:
    with_inputs: bool

class OperationNameVariables:
    id: Optional[str]
    input: ExampleInput
    ids: List[str]
    ids2: Optional[List[Optional[str]]]
    ids3: Optional[List[Optional[List[Optional[str]]]]]

class PersonInput:
    name: str

class ExampleInput:
    id: str
    name: str
    age: int
    person: Optional[PersonInput]
    people: Optional[PersonInput]
    optional_people: Optional[Optional[PersonInput]]
