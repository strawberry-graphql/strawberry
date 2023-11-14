from typing import Union

class AnimalProjection:
    # typename: Animal
    age: int

class OperationNameResultUnionPerson:
    # typename: Person
    name: str

OperationNameResultUnion = Union[AnimalProjection, OperationNameResultUnionPerson]

class OperationNameResultOptionalUnionPerson:
    # typename: Person
    name: str

OperationNameResultOptionalUnion = Union[AnimalProjection, OperationNameResultOptionalUnionPerson]

class OperationNameResult:
    union: OperationNameResultUnion
    optionalUnion: OperationNameResultOptionalUnion
