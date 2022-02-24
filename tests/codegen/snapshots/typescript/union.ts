type OperationNameResultUnionAnimal = {
    age: number
}

type OperationNameResultUnionPerson = {
    name: string
}

type OperationNameResultUnion = OperationNameResultUnionAnimal | OperationNameResultUnionPerson

type OperationNameResult = {
    union: OperationNameResultUnion
}
