import re
import textwrap
from typing import Annotated, Generic, TypeVar, Union

import pytest

import strawberry
from strawberry.exceptions import UndecoratedSubclassError

T = TypeVar("T")


@strawberry.type
class LazyAnimal:
    name: str


class LazyDog(LazyAnimal):
    breed: str


def test_undecorated_subclass_used_as_field_type_raises():
    @strawberry.type
    class Animal:
        name: str

    class Dog(Animal):
        breed: str

    @strawberry.type
    class Query:
        dog: Dog

    with pytest.raises(UndecoratedSubclassError) as exc_info:
        strawberry.Schema(query=Query)

    assert exc_info.value.cls is Dog
    assert exc_info.value.parent is Animal
    assert exc_info.value.suggestion == (
        "Decorate `Dog` with `@strawberry.type`, or use `Animal` instead of `Dog` "
        "in your annotations. Otherwise `Dog` would be published as `Animal`, "
        "without the fields it declares itself."
    )


@pytest.mark.raises_strawberry_exception(
    UndecoratedSubclassError,
    match=re.escape(
        "`Dog` subclasses the Strawberry type `Animal` but isn't decorated itself, "
        "so it can't be used in the schema"
    ),
)
def test_undecorated_subclass_used_as_resolver_return_type_raises():
    @strawberry.type
    class Animal:
        name: str

    class Dog(Animal):
        breed: str

    @strawberry.type
    class Query:
        @strawberry.field
        def dog(self) -> list[Dog | None] | None:
            return None

    strawberry.Schema(query=Query)


def test_undecorated_subclass_of_an_input_used_as_argument_type_raises():
    @strawberry.input
    class AnimalInput:
        name: str

    class DogInput(AnimalInput):
        breed: str

    @strawberry.type
    class Query:
        @strawberry.field
        def name(self, data: DogInput | None = None) -> str:
            return "Rex"

    with pytest.raises(
        UndecoratedSubclassError,
        match=re.escape(
            "`DogInput` subclasses the Strawberry input type `AnimalInput` but "
            "isn't decorated itself"
        ),
    ) as exc_info:
        strawberry.Schema(query=Query)

    assert "`@strawberry.input`" in exc_info.value.suggestion


def test_undecorated_subclass_used_as_input_field_type_raises():
    @strawberry.input
    class AnimalInput:
        name: str

    class DogInput(AnimalInput):
        breed: str

    @strawberry.input
    class Filter:
        animals: list[DogInput]

    @strawberry.type
    class Query:
        @strawberry.field
        def name(self, filter: Filter) -> str:
            return "Rex"

    with pytest.raises(UndecoratedSubclassError, match="`DogInput` subclasses"):
        strawberry.Schema(query=Query)


def test_undecorated_subclass_of_an_interface_raises():
    @strawberry.interface
    class Animal:
        name: str

    class Dog(Animal):
        breed: str

    @strawberry.type
    class Query:
        dog: Dog

    with pytest.raises(
        UndecoratedSubclassError,
        match="`Dog` subclasses the Strawberry interface `Animal`",
    ) as exc_info:
        strawberry.Schema(query=Query)

    assert "`@strawberry.type`" in exc_info.value.suggestion


def test_undecorated_subclass_used_in_union_raises():
    @strawberry.type
    class Animal:
        name: str

    class Dog(Animal):
        breed: str

    @strawberry.type
    class Cat:
        name: str

    @strawberry.type
    class Query:
        pet: Annotated[Union[Dog, Cat], strawberry.union("Pet")]

    with pytest.raises(UndecoratedSubclassError, match="`Dog` subclasses"):
        strawberry.Schema(query=Query)


def test_undecorated_subclass_passed_to_schema_types_raises():
    @strawberry.type
    class Animal:
        name: str

    class Dog(Animal):
        breed: str

    @strawberry.type
    class Query:
        animal: Animal

    with pytest.raises(UndecoratedSubclassError, match="`Dog` subclasses"):
        strawberry.Schema(query=Query, types=[Dog])


def test_undecorated_subclass_used_as_lazy_type_raises():
    @strawberry.type
    class Query:
        dog: Annotated["LazyDog", strawberry.lazy(__name__)]

    with pytest.raises(UndecoratedSubclassError, match="`LazyDog` subclasses"):
        strawberry.Schema(query=Query)


@pytest.mark.parametrize("root", ["query", "mutation", "subscription"])
def test_undecorated_subclass_used_as_root_type_raises(root: str):
    @strawberry.type
    class BaseRoot:
        name: str

    class Root(BaseRoot):
        other: str

    @strawberry.type
    class Query:
        name: str

    roots = {"query": Query, root: Root}

    with pytest.raises(UndecoratedSubclassError, match="`Root` subclasses"):
        strawberry.Schema(**roots)


def test_undecorated_subclass_used_as_federation_query_raises():
    @strawberry.type
    class BaseQuery:
        name: str

    class Query(BaseQuery):
        other: str

    with pytest.raises(UndecoratedSubclassError, match="`Query` subclasses"):
        strawberry.federation.Schema(query=Query)


def test_undecorated_subclass_of_a_generic_type_raises():
    @strawberry.type
    class Edge(Generic[T]):
        node: T

    class NamedEdge(Edge[T]):
        name: str

    # `NamedEdge[int]` is specialized when the type using it is created
    with pytest.raises(
        UndecoratedSubclassError,
        match="`NamedEdge` subclasses the Strawberry type `Edge`",
    ):

        @strawberry.type
        class Query:
            edge: NamedEdge[int]


def test_undecorated_subclass_of_a_specialized_generic_type_raises():
    @strawberry.type
    class Edge(Generic[T]):
        node: T

    class IntEdge(Edge[int]):
        pass

    @strawberry.type
    class Query:
        edge: IntEdge

    with pytest.raises(
        UndecoratedSubclassError,
        match="`IntEdge` subclasses the Strawberry type `Edge`",
    ):
        strawberry.Schema(query=Query)


def test_decorated_subclasses_are_allowed():
    @strawberry.interface
    class Node:
        id: strawberry.ID

    @strawberry.type
    class Animal(Node):
        name: str

    # undecorated classes can still be used to share code between decorated ones
    class Mixin(Animal):
        def describe(self) -> str:
            return self.name

    @strawberry.type
    class Dog(Mixin):
        breed: str

    @strawberry.input
    class DogInput:
        breed: str

    @strawberry.input
    class LabradorInput(DogInput):
        color: str

    @strawberry.type
    class Query:
        animal: Animal
        dog: Dog

        @strawberry.field
        def labrador(self, data: LabradorInput) -> Dog:
            return Dog(id=strawberry.ID("1"), name="Rex", breed=data.breed)

    schema = strawberry.Schema(query=Query)

    assert str(schema) == textwrap.dedent(
        """\
        type Animal implements Node {
          id: ID!
          name: String!
        }

        type Dog implements Node {
          id: ID!
          name: String!
          breed: String!
        }

        input LabradorInput {
          breed: String!
          color: String!
        }

        interface Node {
          id: ID!
        }

        type Query {
          animal: Animal!
          dog: Dog!
          labrador(data: LabradorInput!): Dog!
        }"""
    )


def test_generic_types_are_allowed():
    @strawberry.type
    class Edge(Generic[T]):
        node: T

    @strawberry.type
    class Connection(Generic[T]):
        edges: list[Edge[T]]

    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class NamedUserEdge(Edge[User]):
        cursor: str

    @strawberry.type
    class Query:
        int_edge: Edge[int]
        users: Connection[User]
        user_edge: NamedUserEdge

    schema = strawberry.Schema(query=Query, types=[Edge[str]])

    assert str(schema) == textwrap.dedent(
        """\
        type IntEdge {
          node: Int!
        }

        type NamedUserEdge {
          node: User!
          cursor: String!
        }

        type Query {
          intEdge: IntEdge!
          users: UserConnection!
          userEdge: NamedUserEdge!
        }

        type StrEdge {
          node: String!
        }

        type User {
          name: String!
        }

        type UserConnection {
          edges: [UserEdge!]!
        }

        type UserEdge {
          node: User!
        }"""
    )


def test_resolvers_can_return_instances_of_undecorated_subclasses():
    @strawberry.type
    class Animal:
        name: str

    class Dog(Animal):
        @property
        def loud_name(self) -> str:
            return self.name.upper()

    @strawberry.interface
    class Pet:
        name: str

    @strawberry.type
    class Cat(Pet):
        lives: int

    class HouseCat(Cat):
        pass

    @strawberry.type
    class Query:
        @strawberry.field
        def animal(self) -> Animal:
            return Dog(name="Rex")

        @strawberry.field
        def pet(self) -> Pet:
            return HouseCat(name="Tom", lives=9)

        @strawberry.field
        def pets(self) -> list[Cat | Animal]:
            return [HouseCat(name="Tom", lives=9), Dog(name="Rex")]

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        """
        {
            animal { name }
            pet { __typename name ... on Cat { lives } }
            pets { __typename ... on Cat { lives } ... on Animal { name } }
        }
        """
    )

    assert not result.errors
    assert result.data == {
        "animal": {"name": "Rex"},
        "pet": {"__typename": "Cat", "name": "Tom", "lives": 9},
        "pets": [
            {"__typename": "Cat", "lives": 9},
            {"__typename": "Animal", "name": "Rex"},
        ],
    }
