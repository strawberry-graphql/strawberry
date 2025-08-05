type OperationNameResultOptionalListOfPeople = {
    name: string
    age: number
}

type OperationNameResult = {
    optional_list_of_people: OperationNameResultOptionalListOfPeople[] | undefined
}
