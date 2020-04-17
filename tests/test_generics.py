import typing

import strawberry
from graphql import graphql_sync


def test_supports_generic_simple_type():
    T = typing.TypeVar("T")

    # TODO: we should forbid this to be used directly
    @strawberry.type
    class Edge(typing.Generic[T]):
        cursor: strawberry.ID
        node: T

    @strawberry.type
    class Query:
        @strawberry.field
        def int_edge(self, info, **kwargs) -> Edge[int]:
            return Edge(cursor=strawberry.ID("1"), node=1)

    schema = strawberry.Schema(query=Query)

    query = """{
        intEdge {
            __typename
            cursor
            node
        }
    }"""

    result = graphql_sync(schema, query)

    assert not result.errors
    assert result.data == {
        "intEdge": {"__typename": "IntEdge", "cursor": "1", "node": 1}
    }


def test_supports_generic():
    T = typing.TypeVar("T")

    @strawberry.type
    class Edge(typing.Generic[T]):
        cursor: strawberry.ID
        node: T

    @strawberry.type
    class Person:
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def person_edge(self, info, **kwargs) -> Edge[Person]:
            return Edge(cursor=strawberry.ID("1"), node=Person(name="Example"))

    schema = strawberry.Schema(query=Query)

    query = """{
        personEdge {
            __typename
            cursor
            node {
                name
            }
        }
    }"""

    result = graphql_sync(schema, query)

    assert not result.errors
    assert result.data == {
        "personEdge": {
            "__typename": "PersonEdge",
            "cursor": "1",
            "node": {"name": "Example"},
        }
    }


def test_supports_multiple_generic():
    A = typing.TypeVar("A")
    B = typing.TypeVar("B")

    @strawberry.type
    class Multiple(typing.Generic[A, B]):
        a: A
        b: B

    @strawberry.type
    class Query:
        @strawberry.field
        def multiple(self, info, **kwargs) -> Multiple[int, str]:
            return Multiple(a=123, b="123")

    schema = strawberry.Schema(query=Query)

    query = """{
        multiple {
            __typename
            a
            b
        }
    }"""

    result = graphql_sync(schema, query)

    assert not result.errors
    assert result.data == {
        "multiple": {"__typename": "IntStrMultiple", "a": 123, "b": "123"}
    }


def test_support_nested_generics():
    T = typing.TypeVar("T")

    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Edge(typing.Generic[T]):
        node: T

    @strawberry.type
    class Connection(typing.Generic[T]):
        edge: Edge[T]

    @strawberry.type
    class Query:
        @strawberry.field
        def users(self, info, **kwargs) -> Connection[User]:
            return Connection(edge=Edge(node=User("Patrick")))

    schema = strawberry.Schema(query=Query)

    query = """{
        users {
            __typename
            edge {
                __typename
                node {
                    name
                }
            }
        }
    }"""

    result = graphql_sync(schema, query)

    assert not result.errors
    assert result.data == {
        "users": {
            "__typename": "UserConnection",
            "edge": {"__typename": "UserEdge", "node": {"name": "Patrick"}},
        }
    }


def test_supports_optional():
    T = typing.TypeVar("T")

    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Edge(typing.Generic[T]):
        node: typing.Optional[T] = None

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self, info, **kwargs) -> Edge[User]:
            return Edge()

    schema = strawberry.Schema(query=Query)

    query = """{
        user {
            __typename
            node {
                name
            }
        }
    }"""

    result = graphql_sync(schema, query)

    assert not result.errors
    assert result.data == {"user": {"__typename": "UserEdge", "node": None}}


def test_supports_lists():
    T = typing.TypeVar("T")

    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Edge(typing.Generic[T]):
        nodes: typing.List[T]

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self, info, **kwargs) -> Edge[User]:
            return Edge(nodes=[])

    schema = strawberry.Schema(query=Query)

    query = """{
        user {
            __typename
            nodes {
                name
            }
        }
    }"""

    result = graphql_sync(schema, query)

    assert not result.errors
    assert result.data == {"user": {"__typename": "UserEdge", "nodes": []}}


def test_supports_lists_of_optionals():
    T = typing.TypeVar("T")

    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Edge(typing.Generic[T]):
        nodes: typing.List[typing.Optional[T]]

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self, info, **kwargs) -> Edge[User]:
            return Edge(nodes=[None])

    schema = strawberry.Schema(query=Query)

    query = """{
        user {
            __typename
            nodes {
                name
            }
        }
    }"""

    result = graphql_sync(schema, query)

    assert not result.errors
    assert result.data == {"user": {"__typename": "UserEdge", "nodes": [None]}}


def test_can_extend_generics():
    T = typing.TypeVar("T")

    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Edge(typing.Generic[T]):
        node: T

    @strawberry.type
    class Connection(typing.Generic[T]):
        edges: typing.List[Edge[T]]

    @strawberry.type
    class ConnectionWithMeta(Connection[T]):
        meta: str

    @strawberry.type
    class Query:
        @strawberry.field
        def users(self, info, **kwargs) -> ConnectionWithMeta[User]:
            return ConnectionWithMeta(meta="123", edges=[Edge(node=User("Patrick"))])

    schema = strawberry.Schema(query=Query)

    query = """{
        users {
            __typename
            meta
            edges {
                __typename
                node {
                    name
                }
            }
        }
    }"""

    result = graphql_sync(schema, query)

    assert not result.errors
    assert result.data == {
        "users": {
            "__typename": "UserConnectionWithMeta",
            "meta": "123",
            "edges": [{"__typename": "UserEdge", "node": {"name": "Patrick"}}],
        }
    }
