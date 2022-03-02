type OperationNameResult = {
    with_inputs: boolean
}

type OperationNameVariables = {
    id: string | undefined
    input: ExampleInput
    ids: string[]
    ids2: (string | undefined)[] | undefined
    ids3: ((string | undefined)[] | undefined)[] | undefined
}

type PersonInput = {
    name: string
}

type ExampleInput = {
    id: string
    name: string
    age: number
    person: PersonInput | undefined
    people: PersonInput | undefined
    optional_people: PersonInput | undefined | undefined
}
