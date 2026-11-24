enum SortOrder {
    ASC = "ASC",
    DESC = "DESC",
}

type OperationNameResult = {
    order: SortOrder
}

type SearchInput = {
    order: SortOrder
}

type OperationNameVariables = {
    input: SearchInput
}
