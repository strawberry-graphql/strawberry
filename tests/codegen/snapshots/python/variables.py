from typing_extensions import NotRequired, TypedDict
from typing import List, Optional

class OperationNameResult(TypedDict):
    with_inputs: bool

class PersonInput(TypedDict):
    name: str
    age: NotRequired[Optional[int]]

class ExampleInput(TypedDict):
    id: str
    name: str
    age: int
    person: Optional[PersonInput]
    people: list[PersonInput]
    optional_people: Optional[list[PersonInput]]

class OperationNameVariables(TypedDict):
    id: Optional[str]
    input: ExampleInput
    ids: list[str]
    ids2: Optional[list[Optional[str]]]
    ids3: Optional[list[Optional[list[Optional[str]]]]]
