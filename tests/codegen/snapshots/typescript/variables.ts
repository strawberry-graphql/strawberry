type OperationNameResult = {
    with_inputs: boolean
}

type OperationNameVariables = {
    id: ID | undefined
    input: ExampleInput
    ids: ID[]
    ids2: (ID | undefined)[] | undefined
    ids3: ((ID | undefined)[] | undefined)[] | undefined
}
