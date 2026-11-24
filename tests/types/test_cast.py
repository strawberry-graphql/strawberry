from typing import Generic, TypeVar

import pytest

import strawberry
from strawberry.types.cast import get_strawberry_type_cast


def test_cast():
    @strawberry.type
    class SomeType: ...

    class OtherType: ...

    obj = OtherType
    assert get_strawberry_type_cast(obj) is None

    cast_obj = strawberry.cast(SomeType, obj)
    assert cast_obj is obj
    assert get_strawberry_type_cast(cast_obj) is SomeType


def test_cast_none_obj():
    @strawberry.type
    class SomeType: ...

    obj = None
    assert get_strawberry_type_cast(obj) is None

    cast_obj = strawberry.cast(SomeType, obj)
    assert cast_obj is None
    assert get_strawberry_type_cast(obj) is None


def test_cast_objects_in_unions():
    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Error:
        message: str

    @strawberry.type
    class Other:
        value: int

    class Row:
        # e.g. a row of an ORM
        name = "Ada"
        message = "Oops"

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User | Error:
            return strawberry.cast(User, Row())

        @strawberry.field
        def error(self) -> User | Error:
            return strawberry.cast(Error, Row())

        @strawberry.field
        def other(self) -> User | Error:
            return strawberry.cast(Other, Row())

    schema = strawberry.Schema(query=Query, types=[Other])

    result = schema.execute_sync(
        "{ user { __typename ... on User { name } } "
        "error { __typename ... on Error { message } } }"
    )

    assert not result.errors
    assert result.data == {
        "user": {"__typename": "User", "name": "Ada"},
        "error": {"__typename": "Error", "message": "Oops"},
    }

    result = schema.execute_sync("{ other { __typename } }")

    assert result.errors
    assert 'cannot be resolved for the field "other"' in result.errors[0].message


def test_cast_wins_over_is_type_of_in_unions():
    @strawberry.type
    class User:
        name: str

        @classmethod
        def is_type_of(cls, obj: object, info: strawberry.Info) -> bool:
            return True

    @strawberry.type
    class Error:
        name: str

    class Row:
        name = "Ada"

    @strawberry.type
    class Query:
        @strawberry.field
        def result(self) -> User | Error:
            return strawberry.cast(Error, Row())

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ result { __typename } }")

    assert not result.errors
    assert result.data == {"result": {"__typename": "Error"}}


def test_cast_to_a_generic_type_in_unions():
    T = TypeVar("T")

    @strawberry.type
    class Edge(Generic[T]):
        node: T

    @strawberry.type
    class Error:
        message: str

    class Row:
        node = 1

    @strawberry.type
    class Query:
        @strawberry.field
        def edge(self) -> Edge[int] | Error:
            return strawberry.cast(Edge, Row())

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ edge { __typename ... on IntEdge { node } } }")

    assert not result.errors
    assert result.data == {"edge": {"__typename": "IntEdge", "node": 1}}


def test_cast_to_a_generic_type_implementing_an_interface():
    T = TypeVar("T")

    @strawberry.interface
    class Node:
        id: strawberry.ID

    @strawberry.type
    class Edge(Node, Generic[T]):
        node: T

    @strawberry.type
    class Error:
        message: str

    class Row:
        id = "1"
        node = 1

    @strawberry.type
    class Query:
        @strawberry.field
        def edge(self) -> Edge[int] | Error:
            return strawberry.cast(Edge, Row())

        @strawberry.field
        def node(self) -> Node:
            return strawberry.cast(Edge, Row())

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        "{ edge { __typename ... on IntEdge { id node } } node { __typename id } }"
    )

    assert not result.errors
    assert result.data == {
        "edge": {"__typename": "IntEdge", "id": "1", "node": 1},
        "node": {"__typename": "IntEdge", "id": "1"},
    }


def test_objects_cast_to_an_interface_in_unions():
    @strawberry.interface
    class Node:
        id: strawberry.ID

    @strawberry.type
    class User(Node):
        name: str

    @strawberry.type
    class Error:
        message: str

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User | Error:
            # the cast is used when the object is returned as a `Node`, but must not
            # break returning it in a union
            return strawberry.cast(Node, User(id=strawberry.ID("1"), name="Ada"))

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ user { __typename ... on User { name } } }")

    assert not result.errors
    assert result.data == {"user": {"__typename": "User", "name": "Ada"}}


@pytest.mark.parametrize("implements_an_interface", [True, False])
def test_ambiguous_casts_to_a_generic_type_in_unions(implements_an_interface: bool):
    T = TypeVar("T")

    @strawberry.interface
    class Node:
        id: strawberry.ID

    @strawberry.type
    class Edge(*((Node,) if implements_an_interface else ()), Generic[T]):  # type: ignore[misc]
        node: T

    class Row:
        id = "1"
        node = 1

    @strawberry.type
    class Query:
        @strawberry.field
        def edge(self) -> Edge[int] | Edge[str]:
            return strawberry.cast(Edge, Row())

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ edge { __typename } }")

    assert result.errors
    assert result.errors[0].message == (
        'The object returned for the field "edge" is cast to "Edge", which matches '
        "more than one of its possible types: IntEdge, StrEdge. Return an instance "
        "of one of these types instead."
    )


def test_ambiguous_casts_to_a_generic_type_in_interfaces():
    T = TypeVar("T")

    @strawberry.interface
    class Node:
        id: strawberry.ID

    @strawberry.type
    class Edge(Node, Generic[T]):
        node: T

    class Row:
        id = "1"
        node = 1

    @strawberry.type
    class Query:
        @strawberry.field
        def node(self) -> Node:
            return strawberry.cast(Edge, Row())

    schema = strawberry.Schema(query=Query, types=[Edge[int], Edge[str]])

    result = schema.execute_sync("{ node { __typename } }")

    assert result.errors
    assert result.errors[0].message.startswith(
        'The object returned for the field "node" is cast to "Edge", which matches '
        "more than one of its possible types: IntEdge, StrEdge."
    )


def test_objects_cast_to_a_type_are_resolved_through_interfaces():
    @strawberry.interface
    class Node:
        id: strawberry.ID

    @strawberry.type
    class User(Node):
        name: str

    @strawberry.type
    class Admin(Node):
        name: str

    class Row:
        id = "1"
        name = "Ada"

    @strawberry.type
    class Query:
        @strawberry.field
        def node(self) -> Node:
            return strawberry.cast(Admin, Row())

    schema = strawberry.Schema(query=Query, types=[User, Admin])

    result = schema.execute_sync("{ node { __typename } }")

    assert not result.errors
    assert result.data == {"node": {"__typename": "Admin"}}
