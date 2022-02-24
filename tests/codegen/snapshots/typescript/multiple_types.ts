type OperationNameResultPerson = {
    name: string
}

type OperationNameResultListOfPeople = {
    name: string
}

type OperationNameResult = {
    person: OperationNameResultPerson
    list_of_people: OperationNameResultListOfPeople[]
}
