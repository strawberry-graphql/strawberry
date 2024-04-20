type OperationNameResult = {
    with_inputs: boolean
}

type PersonInput = {
    name: string
    age: number | undefined
}

type ExampleInput = {
    id: string
    name: string
    age: number
    person: PersonInput | undefined
    people: PersonInput[]
    optional_people: PersonInput[] | undefined
}

type OperationNameVariables = {
    id: string | undefined
    input: ExampleInput
    ids: string[]
    ids2: (string | undefined)[] | undefined
    ids3: ((string | undefined)[] | undefined)[] | undefined
}
