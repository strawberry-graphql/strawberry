from typing_extensions import TypedDict

class OperationNameResultUnionAnimal(TypedDict):
    # typename: Animal
    age: int
    name: str

class OperationNameResult(TypedDict):
    union: OperationNameResultUnionAnimal
