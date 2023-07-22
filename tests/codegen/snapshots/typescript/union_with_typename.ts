type OperationNameResultUnionAnimal = {
    age: number
}

type OperationNameResultUnionPerson = {
    name: string
}

type OperationNameResultUnion = OperationNameResultUnionAnimal | OperationNameResultUnionPerson

type OperationNameResultOptionalUnionAnimal = {
    age: number
}

type OperationNameResultOptionalUnionPerson = {
    name: string
}

type OperationNameResultOptionalUnion = OperationNameResultOptionalUnionAnimal | OperationNameResultOptionalUnionPerson

type OperationNameResult = {
    __typename: string
    union: OperationNameResultUnion
    optional_union: OperationNameResultOptionalUnion | undefined
}
