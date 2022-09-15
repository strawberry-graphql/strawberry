import datetime
import decimal
import enum
from typing import TYPE_CHECKING, List, NewType, Optional
from uuid import UUID

import pytest

from typing_extensions import Annotated

import strawberry


if TYPE_CHECKING:

    from .lazy_type import LaziestType

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


@strawberry.input
class PersonInput:
    name: str


@strawberry.input
class ExampleInput:
    id: strawberry.ID
    name: str
    age: int
    person: Optional[PersonInput]
    people: List[PersonInput]
    optional_people: Optional[List[PersonInput]]


@strawberry.type
class Query:
    id: strawberry.ID
    integer: int
    float: float
    boolean: bool
    uuid: UUID
    date: datetime.date
    datetime: datetime.datetime
    time: datetime.time
    decimal: decimal.Decimal
    optional_int: Optional[int]
    list_of_int: List[int]
    list_of_optional_int: List[Optional[int]]
    optional_list_of_optional_int: Optional[List[Optional[int]]]
    person: Person
    optional_person: Optional[Person]
    list_of_people: List[Person]
    enum: Color
    json: JSON
    union: PersonOrAnimal
    optional_union: Optional[PersonOrAnimal]
    interface: Node
    lazy: Annotated["LaziestType", strawberry.lazy("tests.codegen.lazy_type")]

    @strawberry.field
    def with_inputs(self, id: Optional[strawberry.ID], input: ExampleInput) -> bool:
        return True


@pytest.fixture
def schema():
    return strawberry.Schema(query=Query, types=[BlogPost, Image])
