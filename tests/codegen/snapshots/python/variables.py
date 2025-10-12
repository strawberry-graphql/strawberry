from typing import List

class OperationNameResult:
    with_inputs: bool

class PersonInput:
    name: str
    age: int | None = None

class ExampleInput:
    id: str
    name: str
    age: int
    person: PersonInput | None
    people: list[PersonInput]
    optional_people: list[PersonInput] | None

class OperationNameVariables:
    id: str | None
    input: ExampleInput
    ids: list[str]
    ids2: list[str | None] | None
    ids3: list[list[str | None] | None] | None
