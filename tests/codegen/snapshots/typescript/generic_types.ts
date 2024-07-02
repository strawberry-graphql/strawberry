type ListLifeGenericResultListLifeItems1 = {
    name: string
    age: number
}

type ListLifeGenericResultListLifeItems2 = {
    name: string
    age: number
}

type ListLifeGenericResultListLife = {
    items1: ListLifeGenericResultListLifeItems1[]
    items2: ListLifeGenericResultListLifeItems2[]
}

type ListLifeGenericResult = {
    list_life: ListLifeGenericResultListLife
}
