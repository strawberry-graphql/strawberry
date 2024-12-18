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
    people: list[PersonInput]
    optional_people: Optional[list[PersonInput]]

class OperationNameVariables:
    id: Optional[str]
    input: ExampleInput
    ids: list[str]
    ids2: Optional[list[Optional[str]]]
    ids3: Optional[list[Optional[list[Optional[str]]]]]
