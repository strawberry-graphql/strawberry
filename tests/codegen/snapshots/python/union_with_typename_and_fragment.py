from typing_extensions import TypedDict
from typing import Optional, Union

class AnimalProjection(TypedDict):
    # typename: Animal
    age: int

class OperationNameResultUnionPerson(TypedDict):
    # typename: Person
    name: str

OperationNameResultUnion = Union[AnimalProjection, OperationNameResultUnionPerson]

class OperationNameResultOptionalUnionPerson(TypedDict):
    # typename: Person
    name: str

OperationNameResultOptionalUnion = Union[AnimalProjection, OperationNameResultOptionalUnionPerson]

class OperationNameResult(TypedDict):
    union: OperationNameResultUnion
    optional_union: Optional[OperationNameResultOptionalUnion]
