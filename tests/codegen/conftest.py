import datetime
import decimal
import enum
import random
from typing import TYPE_CHECKING, Generic, List, NewType, Optional, TypeVar, Union
from typing_extensions import Annotated
from uuid import UUID

import pytest

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


LivingThing1 = TypeVar("LivingThing1")
LivingThing2 = TypeVar("LivingThing2")


@strawberry.type
class LifeContainer(Generic[LivingThing1, LivingThing2]):
    items1: List[LivingThing1]
    items2: List[LivingThing2]


PersonOrAnimal = Annotated[Union[Person, Animal], strawberry.union("PersonOrAnimal")]


@strawberry.interface
class Node:
    id: str


@strawberry.type
class BlogPost(Node):
    title: str

    def __init__(self, id: str, title: str) -> None:
        self.id = id
        self.title = title


@strawberry.type
class Image(Node):
    url: str


@strawberry.input
class PersonInput:
    name: str
    age: Optional[int] = strawberry.UNSET


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

    @strawberry.field
    def get_person_or_animal(self) -> Union[Person, Animal]:
        """Randomly get a person or an animal."""
        p_or_a = random.choice([Person, Animal])()  # noqa: S311
        p_or_a.name = "Howard"
        p_or_a.age = 7
        return p_or_a

    @strawberry.field
    def list_life() -> LifeContainer[Person, Animal]:
        """Get lists of living things."""
        person = Person(name="Henry", age=10)
        dinosaur = Animal(name="rex", age=66_000_000)
        return LifeContainer([person], [dinosaur])


@strawberry.input
class BlogPostInput:
    title: str = "I replaced my doorbell.  You wouldn't believe what happened next!"
    color: Color = Color.RED
    pi: float = 3.14159
    a_bool: bool = True
    an_int: int = 42
    an_optional_int: Optional[int] = None


@strawberry.input
class AddBlogPostsInput:
    posts: List[BlogPostInput]


@strawberry.type
class AddBlogPostsOutput:
    posts: List[BlogPost]


@strawberry.type
class Mutation:
    @strawberry.mutation
    def add_book(self, name: str) -> BlogPost:
        return BlogPost(id="c6f1c3ce-5249-4570-9182-c2836b836d14", name=name)

    @strawberry.mutation
    def add_blog_posts(self, input: AddBlogPostsInput) -> AddBlogPostsOutput:
        output = AddBlogPostsOutput()
        output.posts = []
        for i, title in enumerate(input.posts):
            output.posts.append(BlogPost(str(i), title))
        return output


@pytest.fixture
def schema() -> strawberry.Schema:
    return strawberry.Schema(query=Query, mutation=Mutation, types=[BlogPost, Image])
