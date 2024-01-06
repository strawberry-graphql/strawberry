type AnimalProjection = {
    age: number
}

type OperationNameResultUnionPerson = {
    name: string
}

type OperationNameResultUnion = AnimalProjection | OperationNameResultUnionPerson

type OperationNameResultOptionalUnionPerson = {
    name: string
}

type OperationNameResultOptionalUnion = AnimalProjection | OperationNameResultOptionalUnionPerson

type OperationNameResult = {
    __typename: string
    union: OperationNameResultUnion
    optional_union: OperationNameResultOptionalUnion | undefined
}
