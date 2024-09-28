type OneOfTypenameTestResultOneOfTypenamePerson = {
    name: string
    age: number
}

type OneOfTypenameTestResult = {
    // alias for one_of_typename
    alias: OneOfTypenameTestResultOneOfTypenamePerson
}

type OneOfInput = {
    a: string,
    b: never
} | {
    a: never,
    b: string
}

type OneOfTypenameTestVariables = {
    value: OneOfInput
}
