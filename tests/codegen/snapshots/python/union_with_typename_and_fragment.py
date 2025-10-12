
class AnimalProjection:
    # typename: Animal
    age: int

class OperationNameResultUnionPerson:
    # typename: Person
    name: str

OperationNameResultUnion = AnimalProjection | OperationNameResultUnionPerson

class OperationNameResultOptionalUnionPerson:
    # typename: Person
    name: str

OperationNameResultOptionalUnion = AnimalProjection | OperationNameResultOptionalUnionPerson

class OperationNameResult:
    union: OperationNameResultUnion
    optional_union: OperationNameResultOptionalUnion | None
