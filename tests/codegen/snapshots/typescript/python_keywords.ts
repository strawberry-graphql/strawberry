enum Clause {
    from = "from",
    WHERE = "WHERE",
}

type OperationNameResult = {
    from: string
    // alias for id
    import: string
    clause: Clause
    with_keyword_input: boolean
}

type KeywordInput = {
    class: string
}

type OperationNameVariables = {
    class: KeywordInput
}
