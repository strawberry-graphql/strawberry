from typing import Union

class OperationNameResultUnionAnimal:
    age: int

class OperationNameResultUnionPerson:
    name: str

OperationNameResultUnion = Union[OperationNameResultUnionAnimal, OperationNameResultUnionPerson]

class OperationNameResult:
    union: OperationNameResultUnion
