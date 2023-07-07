from dataclasses import dataclass
from typing import List

import pytest

import strawberry
from strawberry.types.types import StrawberryObjectDefinition


def test_query_interface():
    @strawberry.interface
    class Cheese:
        name: str

    @strawberry.type
    class Swiss(Cheese):
        canton: str

    @strawberry.type
    class Italian(Cheese):
        province: str

    @strawberry.type
    class Root:
        @strawberry.field
        def assortment(self) -> List[Cheese]:
            return [
                Italian(name="Asiago", province="Friuli"),
                Swiss(name="Tomme", canton="Vaud"),
            ]

    schema = strawberry.Schema(query=Root, types=[Swiss, Italian])

    query = """{
        assortment {
            name
            ... on Italian { province }
            ... on Swiss { canton }
        }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["assortment"] == [
        {"name": "Asiago", "province": "Friuli"},
        {"canton": "Vaud", "name": "Tomme"},
    ]


def test_interfaces_can_implement_other_interfaces():
    @strawberry.interface
    class Error:
        message: str

    @strawberry.interface
    class FieldError(Error):
        message: str
        field: str

    @strawberry.type
    class PasswordTooShort(FieldError):
        message: str
        field: str
        fix: str

    @strawberry.type
    class Query:
        @strawberry.field
        def always_error(self) -> Error:
            return PasswordTooShort(
                message="Password Too Short",
                field="Password",
                fix="Choose more characters",
            )

    schema = strawberry.Schema(Query, types=[PasswordTooShort])
    query = """{
        alwaysError {
            ... on Error {
                message
            }
            ... on FieldError {
                field
            }
            ... on PasswordTooShort {
                fix
            }
        }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["alwaysError"] == {
        "message": "Password Too Short",
        "field": "Password",
        "fix": "Choose more characters",
    }


def test_interface_duck_typing():
    @strawberry.interface
    class Entity:
        id: int

    @strawberry.type
    class Anime(Entity):
        name: str

        @classmethod
        def is_type_of(cls, obj, _info) -> bool:
            return isinstance(obj, AnimeORM)

    @dataclass
    class AnimeORM:
        id: int
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def anime(self) -> Anime:
            return AnimeORM(id=1, name="One Piece")  # type: ignore

    schema = strawberry.Schema(query=Query)

    query = """{
        anime { name }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {"anime": {"name": "One Piece"}}


def test_interface_explicit_type_resolution():
    @dataclass
    class AnimeORM:
        id: int
        name: str

    @strawberry.interface
    class Node:
        id: int

    @strawberry.type
    class Anime(Node):
        name: str

        @classmethod
        def is_type_of(cls, obj, _info) -> bool:
            return isinstance(obj, AnimeORM)

    @strawberry.type
    class Query:
        @strawberry.field
        def node(self) -> Node:
            return AnimeORM(id=1, name="One Piece")  # type: ignore

    schema = strawberry.Schema(query=Query, types=[Anime])

    query = "{ node { __typename, id } }"
    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {"node": {"__typename": "Anime", "id": 1}}


@pytest.mark.xfail(reason="We don't support returning dictionaries yet")
def test_interface_duck_typing_returning_dict():
    @strawberry.interface
    class Entity:
        id: int

    @strawberry.type
    class Anime(Entity):
        name: str

    @dataclass
    class AnimeORM:
        id: int
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def anime(self) -> Anime:
            return dict(id=1, name="One Piece")  # type: ignore

    schema = strawberry.Schema(query=Query)

    query = """{
        anime { name }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {"anime": {"name": "One Piece"}}


def test_duplicated_interface_in_multi_inheritance():
    """Test that interfaces are gathered properly via CPython's MRO.

    Previously interfaces were duplicated within a "Diamond Problem" inheritance
    scenario which is tested here. Using the MRO instead of the `__bases__` attribute of
    a class in :py:func:`strawberry.object_type._get_interfaces` allows Python's C3
    linearization algorithm to create a consistent precedents graph without duplicates.
    """

    @strawberry.interface
    class Base:
        id: str

    @strawberry.interface
    class InterfaceA(Base):
        id: str
        field_a: str

    @strawberry.interface
    class InterfaceB(Base):
        id: str
        field_b: str

    @strawberry.type
    class MyType(InterfaceA, InterfaceB):
        id: str
        field_a: str
        field_b: str

    @strawberry.type
    class Query:
        my_type: MyType

    type_definition: StrawberryObjectDefinition = MyType.__strawberry_definition__
    origins = [i.origin for i in type_definition.interfaces]
    assert origins == [InterfaceA, InterfaceB, Base]

    strawberry.Schema(Query)  # Final sanity check to ensure schema compiles
