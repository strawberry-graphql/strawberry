type OperationNameResultLazy = {
    something: boolean
}

type OperationNameResult = {
    id: string
    integer: number
    float: number
    boolean: boolean
    uuid: string
    date: string
    datetime: string
    time: string
    decimal: string
    lazy: OperationNameResultLazy
}
