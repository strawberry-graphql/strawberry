type OperationNameResultPerson = {
    name: string
}

type OperationNameResultListOfPeople = {
    name: string
}

type OperationNameResult = {
    person: OperationNameResultPerson
    listOfPeople: OperationNameResultListOfPeople
}
