from typing import Optional, Union

class OperationNameResultUnionAnimal:
    age: int

class OperationNameResultUnionPerson:
    name: str

OperationNameResultUnion = Union[OperationNameResultUnionAnimal, OperationNameResultUnionPerson]

class OperationNameResultOptionalUnionAnimal:
    age: int

class OperationNameResultOptionalUnionPerson:
    name: str

OperationNameResultOptionalUnion = Union[OperationNameResultOptionalUnionAnimal, OperationNameResultOptionalUnionPerson]

class OperationNameResult:
    union: OperationNameResultUnion
    optional_union: Optional[OperationNameResultOptionalUnion]
