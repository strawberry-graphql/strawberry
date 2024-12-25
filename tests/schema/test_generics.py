import textwrap
from enum import Enum
from typing import Any, Generic, Optional, TypeVar, Union
from typing_extensions import Self

import strawberry


def test_supports_generic_simple_type():
    T = TypeVar("T")

    @strawberry.type
    class Edge(Generic[T]):
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


def test_supports_generic_specialized():
    T = TypeVar("T")

    @strawberry.type
    class Edge(Generic[T]):
        cursor: strawberry.ID
        node_field: T

    @strawberry.type
    class IntEdge(Edge[int]): ...

    @strawberry.type
    class Query:
        @strawberry.field
        def example(self) -> IntEdge:
            return IntEdge(cursor=strawberry.ID("1"), node_field=1)

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


def test_supports_generic_specialized_subclass():
    T = TypeVar("T")

    @strawberry.type
    class Edge(Generic[T]):
        cursor: strawberry.ID
        node_field: T

    @strawberry.type
    class IntEdge(Edge[int]): ...

    @strawberry.type
    class IntEdgeSubclass(IntEdge): ...

    @strawberry.type
    class Query:
        @strawberry.field
        def example(self) -> IntEdgeSubclass:
            return IntEdgeSubclass(cursor=strawberry.ID("1"), node_field=1)

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
        "example": {"__typename": "IntEdgeSubclass", "cursor": "1", "nodeField": 1}
    }


def test_supports_generic_specialized_with_type():
    T = TypeVar("T")

    @strawberry.type
    class Fruit:
        name: str

    @strawberry.type
    class Edge(Generic[T]):
        cursor: strawberry.ID
        node_field: T

    @strawberry.type
    class FruitEdge(Edge[Fruit]): ...

    @strawberry.type
    class Query:
        @strawberry.field
        def example(self) -> FruitEdge:
            return FruitEdge(cursor=strawberry.ID("1"), node_field=Fruit(name="Banana"))

    schema = strawberry.Schema(query=Query)

    query = """{
        example {
            __typename
            cursor
            nodeField {
                name
            }
        }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {
        "example": {
            "__typename": "FruitEdge",
            "cursor": "1",
            "nodeField": {"name": "Banana"},
        }
    }


def test_supports_generic_specialized_with_list_type():
    T = TypeVar("T")

    @strawberry.type
    class Fruit:
        name: str

    @strawberry.type
    class Edge(Generic[T]):
        cursor: strawberry.ID
        nodes: list[T]

    @strawberry.type
    class FruitEdge(Edge[Fruit]): ...

    @strawberry.type
    class Query:
        @strawberry.field
        def example(self) -> FruitEdge:
            return FruitEdge(
                cursor=strawberry.ID("1"),
                nodes=[Fruit(name="Banana"), Fruit(name="Apple")],
            )

    schema = strawberry.Schema(query=Query)

    query = """{
        example {
            __typename
            cursor
            nodes {
                name
            }
        }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {
        "example": {
            "__typename": "FruitEdge",
            "cursor": "1",
            "nodes": [
                {"name": "Banana"},
                {"name": "Apple"},
            ],
        }
    }


def test_supports_generic():
    T = TypeVar("T")

    @strawberry.type
    class Edge(Generic[T]):
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
    A = TypeVar("A")
    B = TypeVar("B")

    @strawberry.type
    class Multiple(Generic[A, B]):
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


def test_supports_optional():
    T = TypeVar("T")

    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Edge(Generic[T]):
        node: Optional[T] = None

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
    T = TypeVar("T")

    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Edge(Generic[T]):
        nodes: list[T]

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
    T = TypeVar("T")

    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Edge(Generic[T]):
        nodes: list[Optional[T]]

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
    T = TypeVar("T")

    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Edge(Generic[T]):
        node: T

    @strawberry.type
    class Connection(Generic[T]):
        edges: list[Edge[T]]

    @strawberry.type
    class ConnectionWithMeta(Connection[T]):
        meta: str

    @strawberry.type
    class Query:
        @strawberry.field
        def users(self) -> ConnectionWithMeta[User]:
            return ConnectionWithMeta(
                meta="123", edges=[Edge(node=User(name="Patrick"))]
            )

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
    T = TypeVar("T")

    @strawberry.type
    class Edge(Generic[T]):
        cursor: strawberry.ID
        node: T

    @strawberry.type
    class Fallback:
        node: str

    @strawberry.type
    class Query:
        @strawberry.field
        def example(self) -> Union[Fallback, Edge[int]]:
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
    T = TypeVar("T")

    @strawberry.type
    class Pet:
        name: str

    @strawberry.type
    class ErrorNode(Generic[T]):
        code: T

    @strawberry.enum
    class Codes(Enum):
        a = "a"
        b = "b"

    @strawberry.type
    class Query:
        @strawberry.field
        def result(self) -> Union[Pet, ErrorNode[Codes]]:
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


def test_generic_with_enum():
    T = TypeVar("T")

    @strawberry.enum
    class EstimatedValueEnum(Enum):
        test = "test"
        testtest = "testtest"

    @strawberry.type
    class EstimatedValue(Generic[T]):
        value: T
        type: EstimatedValueEnum

    @strawberry.type
    class Query:
        @strawberry.field
        def estimated_value(self) -> Optional[EstimatedValue[int]]:
            return EstimatedValue(value=1, type=EstimatedValueEnum.test)

    schema = strawberry.Schema(query=Query)

    query = """{
        estimatedValue {
            __typename
            value
            type
        }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {
        "estimatedValue": {
            "__typename": "IntEstimatedValue",
            "value": 1,
            "type": "test",
        }
    }


def test_supports_generic_in_unions_multiple_vars():
    A = TypeVar("A")
    B = TypeVar("B")

    @strawberry.type
    class Edge(Generic[A, B]):
        info: A
        node: B

    @strawberry.type
    class Fallback:
        node: str

    @strawberry.type
    class Query:
        @strawberry.field
        def example(self) -> Union[Fallback, Edge[int, str]]:
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


def test_supports_multiple_generics_in_union():
    T = TypeVar("T")

    @strawberry.type
    class Edge(Generic[T]):
        cursor: strawberry.ID
        node: T

    @strawberry.type
    class Query:
        @strawberry.field
        def example(self) -> list[Union[Edge[int], Edge[str]]]:
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


def test_generics_via_anonymous_union():
    T = TypeVar("T")

    @strawberry.type
    class Edge(Generic[T]):
        cursor: str
        node: T

    @strawberry.type
    class Connection(Generic[T]):
        edges: list[Edge[T]]

    @strawberry.type
    class Entity1:
        id: int

    @strawberry.type
    class Entity2:
        id: int

    @strawberry.type
    class Query:
        entities: Connection[Union[Entity1, Entity2]]

    schema = strawberry.Schema(query=Query)

    expected_schema = textwrap.dedent(
        """
        type Entity1 {
          id: Int!
        }

        union Entity1Entity2 = Entity1 | Entity2

        type Entity1Entity2Connection {
          edges: [Entity1Entity2Edge!]!
        }

        type Entity1Entity2Edge {
          cursor: String!
          node: Entity1Entity2!
        }

        type Entity2 {
          id: Int!
        }

        type Query {
          entities: Entity1Entity2Connection!
        }
        """
    ).strip()

    assert str(schema) == expected_schema


def test_generated_names():
    T = TypeVar("T")

    @strawberry.type
    class EdgeWithCursor(Generic[T]):
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
    T = TypeVar("T")

    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Edge(Generic[T]):
        nodes: list[T]

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> Union[User, Edge[User]]:
            return Edge(nodes=[User(name="P")])

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
    T = TypeVar("T")

    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Edge(Generic[T]):
        nodes: list[T]

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> Union[User, Edge[User]]:
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
    T = TypeVar("T")

    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Edge(Generic[T]):
        nodes: list[T]

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> Union[User, Edge[User]]:
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

    assert (
        'of the field "user" is not in the list of the types of the union'
        in result.errors[0].message
    )


def test_generic_with_arguments():
    T = TypeVar("T")

    @strawberry.type
    class Collection(Generic[T]):
        @strawberry.field
        def by_id(self, ids: list[int]) -> list[T]:
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


def test_generic_argument():
    T = TypeVar("T")

    @strawberry.type
    class Node(Generic[T]):
        @strawberry.field
        def edge(self, arg: T) -> bool:
            return bool(arg)

        @strawberry.field
        def edges(self, args: list[T]) -> int:
            return len(args)

    @strawberry.type
    class Query:
        i_node: Node[int]
        b_node: Node[bool]

    schema = strawberry.Schema(Query)

    expected_schema = """
    type BoolNode {
      edge(arg: Boolean!): Boolean!
      edges(args: [Boolean!]!): Int!
    }

    type IntNode {
      edge(arg: Int!): Boolean!
      edges(args: [Int!]!): Int!
    }

    type Query {
      iNode: IntNode!
      bNode: BoolNode!
    }
    """

    assert str(schema) == textwrap.dedent(expected_schema).strip()


def test_generic_extra_type():
    T = TypeVar("T")

    @strawberry.type
    class Node(Generic[T]):
        field: T

    @strawberry.type
    class Query:
        name: str

    schema = strawberry.Schema(Query, types=[Node[int]])

    expected_schema = """
    type IntNode {
      field: Int!
    }

    type Query {
      name: String!
    }
    """

    assert str(schema) == textwrap.dedent(expected_schema).strip()


def test_generic_extending_with_type_var():
    T = TypeVar("T")

    @strawberry.interface
    class Node(Generic[T]):
        id: strawberry.ID

        def _resolve(self) -> Optional[T]:
            return None

    @strawberry.type
    class Book(Node[str]):
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def books(self) -> list[Book]:
            return []

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


def test_self():
    @strawberry.interface
    class INode:
        field: Optional[Self]
        fields: list[Self]

    @strawberry.type
    class Node(INode): ...

    schema = strawberry.Schema(query=Node)

    expected_schema = """
    schema {
      query: Node
    }

    interface INode {
      field: INode
      fields: [INode!]!
    }

    type Node implements INode {
      field: Node
      fields: [Node!]!
    }
    """

    assert str(schema) == textwrap.dedent(expected_schema).strip()

    query = """{
        field {
            __typename
        }
        fields {
            __typename
        }
    }"""
    result = schema.execute_sync(query, root_value=Node(field=None, fields=[]))
    assert result.data == {"field": None, "fields": []}


def test_supports_generic_input_type():
    T = TypeVar("T")

    @strawberry.input
    class Input(Generic[T]):
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


def test_generic_interface():
    @strawberry.interface
    class ObjectType:
        obj: strawberry.Private[Any]

        @strawberry.field
        def repr(self) -> str:
            return str(self.obj)

    T = TypeVar("T")

    @strawberry.type
    class GenericObject(ObjectType, Generic[T]):
        @strawberry.field
        def value(self) -> T:
            return self.obj

    @strawberry.type
    class Query:
        @strawberry.field
        def foo(self) -> GenericObject[str]:
            return GenericObject(obj="foo")

    schema = strawberry.Schema(query=Query)
    query_result = schema.execute_sync(
        """
            query {
                foo {
                    __typename
                    value
                    repr
                }
            }
        """
    )

    assert not query_result.errors
    assert query_result.data == {
        "foo": {
            "__typename": "StrGenericObject",
            "value": "foo",
            "repr": "foo",
        }
    }


def test_generic_interface_extra_types():
    T = TypeVar("T")

    @strawberry.interface
    class Abstract:
        x: str = ""

    @strawberry.type
    class Real(Generic[T], Abstract):
        y: T

    @strawberry.type
    class Query:
        @strawberry.field
        def real(self) -> Abstract:
            return Real[int](y=0)

    schema = strawberry.Schema(Query, types=[Real[int]])

    assert (
        str(schema)
        == textwrap.dedent(
            """
            interface Abstract {
              x: String!
            }

            type IntReal implements Abstract {
              x: String!
              y: Int!
            }

            type Query {
              real: Abstract!
            }
            """
        ).strip()
    )

    query_result = schema.execute_sync("{ real { __typename x } }")

    assert not query_result.errors
    assert query_result.data == {"real": {"__typename": "IntReal", "x": ""}}


def test_generic_with_interface():
    T = TypeVar("T")

    @strawberry.type
    class Pagination(Generic[T]):
        items: list[T]

    @strawberry.interface
    class TestInterface:
        data: str

    @strawberry.type
    class Test1(TestInterface):
        pass

    @strawberry.type
    class TestError:
        reason: str

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(
            self, info: strawberry.Info
        ) -> Union[Pagination[TestInterface], TestError]:
            return Pagination(items=[Test1(data="test1")])

    schema = strawberry.Schema(Query, types=[Test1])

    query_result = schema.execute_sync(
        "{ hello { ... on TestInterfacePagination { items { data }} } }"
    )

    assert not query_result.errors
    assert query_result.data == {"hello": {"items": [{"data": "test1"}]}}
