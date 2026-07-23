from typing_extensions import TypedDict
from typing import List

class ListLifeGenericResultListLifeItems1(TypedDict):
    name: str
    age: int

class ListLifeGenericResultListLifeItems2(TypedDict):
    name: str
    age: int

class ListLifeGenericResultListLife(TypedDict):
    items1: list[ListLifeGenericResultListLifeItems1]
    items2: list[ListLifeGenericResultListLifeItems2]

class ListLifeGenericResult(TypedDict):
    list_life: ListLifeGenericResultListLife
