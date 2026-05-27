from typing_extensions import TypedDict
from typing import Optional, Union

class OperationNameResultUnionAnimal(TypedDict):
    # typename: Animal
    age: int

class OperationNameResultUnionPerson(TypedDict):
    # typename: Person
    name: str

OperationNameResultUnion = Union[OperationNameResultUnionAnimal, OperationNameResultUnionPerson]

class OperationNameResultOptionalUnionAnimal(TypedDict):
    # typename: Animal
    age: int

class OperationNameResultOptionalUnionPerson(TypedDict):
    # typename: Person
    name: str

OperationNameResultOptionalUnion = Union[OperationNameResultOptionalUnionAnimal, OperationNameResultOptionalUnionPerson]

class OperationNameResult(TypedDict):
    union: OperationNameResultUnion
    optional_union: Optional[OperationNameResultOptionalUnion]
