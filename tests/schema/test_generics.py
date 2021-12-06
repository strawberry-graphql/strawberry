import textwrap
import typing
from enum import Enum

import pytest

import strawberry


def test_supports_generic_simple_type():
    T = typing.TypeVar("T")

    @strawberry.type
    class Edge(typing.Generic[T]):
        cursor: strawberry.ID
        node_field: T

    @strawberry.type
    class Query:
        @strawberry.field
        def example(self) -> Edge[int]:
            return Edge(cursor=strawberry.ID("1"), node_field=1)

    schema = strawberry.Schema(query=Query)

    query = """{
        example {
            __typename
            cursor
            nodeField
        }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {
        "example": {"__typename": "IntEdge", "cursor": "1", "nodeField": 1}
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
        def example(self) -> Edge[Person]:
            return Edge(cursor=strawberry.ID("1"), node=Person(name="Example"))

    schema = strawberry.Schema(query=Query)

    query = """{
        example {
            __typename
            cursor
            node {
                name
            }
        }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {
        "example": {
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
        def multiple(self) -> Multiple[int, str]:
            return Multiple(a=123, b="123")

    schema = strawberry.Schema(query=Query)

    query = """{
        multiple {
            __typename
            a
            b
        }
    }"""

    result = schema.execute_sync(query)

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
        def users(self) -> Connection[User]:
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

    result = schema.execute_sync(query)

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
        def user(self) -> Edge[User]:
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

    result = schema.execute_sync(query)

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
        def user(self) -> Edge[User]:
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

    result = schema.execute_sync(query)

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
        def user(self) -> Edge[User]:
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

    result = schema.execute_sync(query)

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
        def users(self) -> ConnectionWithMeta[User]:
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

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {
        "users": {
            "__typename": "UserConnectionWithMeta",
            "meta": "123",
            "edges": [{"__typename": "UserEdge", "node": {"name": "Patrick"}}],
        }
    }


def test_supports_generic_in_unions():
    T = typing.TypeVar("T")

    @strawberry.type
    class Edge(typing.Generic[T]):
        cursor: strawberry.ID
        node: T

    @strawberry.type
    class Fallback:
        node: str

    @strawberry.type
    class Query:
        @strawberry.field
        def example(self) -> typing.Union[Fallback, Edge[int]]:
            return Edge(cursor=strawberry.ID("1"), node=1)

    schema = strawberry.Schema(query=Query)

    query = """{
        example {
            __typename

            ... on IntEdge {
                cursor
                node
            }
        }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {
        "example": {"__typename": "IntEdge", "cursor": "1", "node": 1}
    }


def test_generic_with_enum_as_param_of_type_inside_unions():
    T = typing.TypeVar("T")

    @strawberry.type
    class Pet:
        name: str

    @strawberry.type
    class ErrorNode(typing.Generic[T]):
        code: T

    @strawberry.enum
    class Codes(Enum):
        a = "a"
        b = "b"

    @strawberry.type
    class Query:
        @strawberry.field
        def result(self) -> typing.Union[Pet, ErrorNode[Codes]]:
            return ErrorNode(code=Codes.a)

    schema = strawberry.Schema(query=Query)

    query = """{
        result {
            __typename
            ... on CodesErrorNode {
                code
            }
        }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {"result": {"__typename": "CodesErrorNode", "code": "a"}}


def test_supports_generic_in_unions_multiple_vars():
    A = typing.TypeVar("A")
    B = typing.TypeVar("B")

    @strawberry.type
    class Edge(typing.Generic[A, B]):
        info: A
        node: B

    @strawberry.type
    class Fallback:
        node: str

    @strawberry.type
    class Query:
        @strawberry.field
        def example(self) -> typing.Union[Fallback, Edge[int, str]]:
            return Edge(node="string", info=1)

    schema = strawberry.Schema(query=Query)

    query = """{
        example {
            __typename

            ... on IntStrEdge {
                node
                info
            }
        }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {
        "example": {"__typename": "IntStrEdge", "node": "string", "info": 1}
    }


def test_supports_generic_in_unions_with_nesting():
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
    class Fallback:
        node: str

    @strawberry.type
    class Query:
        @strawberry.field
        def users(self) -> typing.Union[Connection[User], Fallback]:
            return Connection(edge=Edge(node=User("Patrick")))

    schema = strawberry.Schema(query=Query)

    query = """{
        users {
            __typename
            ... on UserConnection {
                edge {
                    __typename
                    node {
                        name
                    }
                }
            }
        }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {
        "users": {
            "__typename": "UserConnection",
            "edge": {"__typename": "UserEdge", "node": {"name": "Patrick"}},
        }
    }


def test_supports_multiple_generics_in_union():
    T = typing.TypeVar("T")

    @strawberry.type
    class Edge(typing.Generic[T]):
        cursor: strawberry.ID
        node: T

    @strawberry.type
    class Query:
        @strawberry.field
        def example(self) -> typing.List[typing.Union[Edge[int], Edge[str]]]:
            return [
                Edge(cursor=strawberry.ID("1"), node=1),
                Edge(cursor=strawberry.ID("2"), node="string"),
            ]

    schema = strawberry.Schema(query=Query)

    expected_schema = """
      type IntEdge {
        cursor: ID!
        node: Int!
      }

      union IntEdgeStrEdge = IntEdge | StrEdge

      type Query {
        example: [IntEdgeStrEdge!]!
      }

      type StrEdge {
        cursor: ID!
        node: String!
      }
    """

    assert str(schema) == textwrap.dedent(expected_schema).strip()

    query = """{
        example {
            __typename

            ... on IntEdge {
                cursor
                intNode: node
            }

            ... on StrEdge {
                cursor
                strNode: node
            }
        }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {
        "example": [
            {"__typename": "IntEdge", "cursor": "1", "intNode": 1},
            {"__typename": "StrEdge", "cursor": "2", "strNode": "string"},
        ]
    }


def test_generated_names():
    T = typing.TypeVar("T")

    @strawberry.type
    class EdgeWithCursor(typing.Generic[T]):
        cursor: strawberry.ID
        node: T

    @strawberry.type
    class SpecialPerson:
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def person_edge(self) -> EdgeWithCursor[SpecialPerson]:
            return EdgeWithCursor(
                cursor=strawberry.ID("1"), node=SpecialPerson(name="Example")
            )

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

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {
        "personEdge": {
            "__typename": "SpecialPersonEdgeWithCursor",
            "cursor": "1",
            "node": {"name": "Example"},
        }
    }


def test_supports_lists_within_unions():
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
        def user(self) -> typing.Union[User, Edge[User]]:
            return Edge(nodes=[User("P")])

    schema = strawberry.Schema(query=Query)

    query = """{
        user {
            __typename

            ... on UserEdge {
                nodes {
                    name
                }
            }
        }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {"user": {"__typename": "UserEdge", "nodes": [{"name": "P"}]}}


def test_supports_lists_within_unions_empty_list():
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
        def user(self) -> typing.Union[User, Edge[User]]:
            return Edge(nodes=[])

    schema = strawberry.Schema(query=Query)

    query = """{
        user {
            __typename

            ... on UserEdge {
                nodes {
                    name
                }
            }
        }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {"user": {"__typename": "UserEdge", "nodes": []}}


@pytest.mark.xfail()
def test_raises_error_when_unable_to_find_type():
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
        def user(self) -> typing.Union[User, Edge[User]]:
            return Edge(nodes=["bad example"])  # type: ignore

    schema = strawberry.Schema(query=Query)

    query = """{
        user {
            __typename

            ... on UserEdge {
                nodes {
                    name
                }
            }
        }
    }"""

    result = schema.execute_sync(query)

    assert result.errors[0].message == (
        "Unable to find type for <class 'tests.schema.test_generics."
        "test_raises_error_when_unable_to_find_type.<locals>.Edge'> "
        "and (<class 'str'>,)"
    )


def test_generic_with_arguments():
    T = typing.TypeVar("T")

    @strawberry.type
    class Collection(typing.Generic[T]):
        @strawberry.field
        def by_id(self, ids: typing.List[int]) -> typing.List[T]:
            return []

    @strawberry.type
    class Post:
        name: str

    @strawberry.type
    class Query:
        user: Collection[Post]

    schema = strawberry.Schema(Query)

    expected_schema = """
    type Post {
      name: String!
    }

    type PostCollection {
      byId(ids: [Int!]!): [Post!]!
    }

    type Query {
      user: PostCollection!
    }
    """

    assert str(schema) == textwrap.dedent(expected_schema).strip()


def test_generic_extending_with_type_var():
    T = typing.TypeVar("T")

    @strawberry.interface
    class Node(typing.Generic[T]):
        id: strawberry.ID

        def _resolve(self) -> typing.Optional[T]:
            return None

    @strawberry.type
    class Book(Node[str]):
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def books(self) -> typing.List[Book]:
            return list()

    schema = strawberry.Schema(query=Query)

    expected_schema = """
    type Book implements Node {
      id: ID!
      name: String!
    }

    interface Node {
      id: ID!
    }

    type Query {
      books: [Book!]!
    }
    """

    assert str(schema) == textwrap.dedent(expected_schema).strip()


def test_supports_generic_input_type():
    T = typing.TypeVar("T")

    @strawberry.input
    class Input(typing.Generic[T]):
        field: T

    @strawberry.type
    class Query:
        @strawberry.field
        def field(self, input: Input[str]) -> str:
            return input.field

    schema = strawberry.Schema(query=Query)

    query = """{
        field(input: { field: "data" })
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {"field": "data"}
