import enum
from typing import List, NewType, Optional

import pytest

import strawberry


JSON = strawberry.scalar(NewType("JSON", str))


@strawberry.enum
class Color(enum.Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


@strawberry.type
class Person:
    name: str
    age: int


@strawberry.type
class Animal:
    name: str
    age: int


PersonOrAnimal = strawberry.union("PersonOrAnimal", (Person, Animal))


@strawberry.interface
class Node:
    id: str


@strawberry.type
class BlogPost(Node):
    title: str


@strawberry.type
class Image(Node):
    url: str


@strawberry.type
class Query:
    id: strawberry.ID
    integer: int
    another_integer: int
    optional_int: Optional[int]
    list_of_optional_int: List[Optional[int]]
    person: Person
    optional_person: Optional[Person]
    enum: Color
    json: JSON
    union: PersonOrAnimal
    interface: Node


@pytest.fixture
def schema():
    return strawberry.Schema(query=Query, types=[BlogPost, Image])
