type OperationNameResult = {
    withInputs: boolean
}

type PersonInput = {
    name: string
    age: number
}

type ExampleInput = {
    id: string
    name: string
    age: number
    person: PersonInput
    people: PersonInput
    optionalPeople: PersonInput
}

type OperationNameVariables = {
    id: string | undefined
    input: ExampleInput
    ids: string[]
    ids2: (string | undefined)[] | undefined
    ids3: ((string | undefined)[] | undefined)[] | undefined
}
