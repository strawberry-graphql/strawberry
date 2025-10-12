
class OperationNameResultUnionAnimal:
    # typename: Animal
    age: int

class OperationNameResultUnionPerson:
    # typename: Person
    name: str

OperationNameResultUnion = OperationNameResultUnionAnimal | OperationNameResultUnionPerson

class OperationNameResultOptionalUnionAnimal:
    # typename: Animal
    age: int

class OperationNameResultOptionalUnionPerson:
    # typename: Person
    name: str

OperationNameResultOptionalUnion = OperationNameResultOptionalUnionAnimal | OperationNameResultOptionalUnionPerson

class OperationNameResult:
    union: OperationNameResultUnion
    optional_union: OperationNameResultOptionalUnion | None
