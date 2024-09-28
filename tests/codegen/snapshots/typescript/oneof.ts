type OneOfTestResult = {
    one_of: string
}

type OneOfInput = {
    a: string,
    b: never
} | {
    a: never,
    b: string
}

type OneOfTestVariables = {
    value: OneOfInput
}
