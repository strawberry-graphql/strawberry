type OperationNameResultLazy = {
    // alias for something
    lazy: boolean
}

type OperationNameResult = {
    id: string
    // alias for id
    second_id: string
    // alias for float
    a_float: number
    lazy: OperationNameResultLazy
}
