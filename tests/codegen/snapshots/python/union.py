from typing import Optional, Union

class OperationNameResultUnionAnimal:
    # typename: Animal
    age: int

class OperationNameResultUnionPerson:
    # typename: Person
    name: str

OperationNameResultUnion = Union[OperationNameResultUnionAnimal, OperationNameResultUnionPerson]

class OperationNameResultOptionalUnionAnimal:
    # typename: Animal
    age: int

class OperationNameResultOptionalUnionPerson:
    # typename: Person
    name: str

OperationNameResultOptionalUnion = Union[OperationNameResultOptionalUnionAnimal, OperationNameResultOptionalUnionPerson]

class OperationNameResult:
    union: OperationNameResultUnion
    optional_union: Optional[OperationNameResultOptionalUnion]
