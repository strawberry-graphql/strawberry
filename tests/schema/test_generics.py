import typing

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
        def int_edge(self, info) -> Edge[int]:
            return Edge(cursor=strawberry.ID("1"), node_field=1)

    schema = strawberry.Schema(query=Query)

    query = """{
        intEdge {
            __typename
            cursor
            nodeField
        }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {
        "intEdge": {"__typename": "IntEdge", "cursor": "1", "nodeField": 1}
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
        def person_edge(self, info) -> Edge[Person]:
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

    result = schema.execute_sync(query)

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
        def multiple(self, info) -> Multiple[int, str]:
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
        def users(self, info) -> Connection[User]:
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
        def user(self, info) -> Edge[User]:
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
        def user(self, info) -> Edge[User]:
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
        def user(self, info) -> Edge[User]:
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
        def users(self, info) -> ConnectionWithMeta[User]:
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
        def example(self, info) -> typing.Union[Fallback, Edge[int]]:
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
        def example(self, info) -> typing.Union[Fallback, Edge[int, str]]:
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
        def users(self, info) -> typing.Union[Connection[User], Fallback]:
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
        def example(self, info) -> typing.List[typing.Union[Edge[int], Edge[str]]]:
            return [
                Edge(cursor=strawberry.ID("1"), node=1),
                Edge(cursor=strawberry.ID("2"), node="string"),
            ]

    schema = strawberry.Schema(query=Query)

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
        def person_edge(self, info) -> EdgeWithCursor[SpecialPerson]:
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
        def user(self, info) -> typing.Union[User, Edge[User]]:
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
        def user(self, info) -> typing.Union[User, Edge[User]]:
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
        def user(self, info) -> typing.Union[User, Edge[User]]:
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
