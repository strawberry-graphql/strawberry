from typing import List

class ListLifeGenericResultListLifeItems1:
    name: str
    age: int

class ListLifeGenericResultListLifeItems2:
    name: str
    age: int

class ListLifeGenericResultListLife:
    items1: list[ListLifeGenericResultListLifeItems1]
    items2: list[ListLifeGenericResultListLifeItems2]

class ListLifeGenericResult:
    list_life: ListLifeGenericResultListLife
