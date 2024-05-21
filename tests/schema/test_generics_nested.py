import textwrap
from typing import Generic, List, Optional, TypeVar, Union

import strawberry
from strawberry.scalars import JSON


def test_support_nested_generics():
    T = TypeVar("T")

    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Edge(Generic[T]):
        node: T

    @strawberry.type
    class Connection(Generic[T]):
        edge: Edge[T]

    @strawberry.type
    class Query:
        @strawberry.field
        def users(self) -> Connection[User]:
            return Connection(edge=Edge(node=User(name="Patrick")))

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


def test_unions_nested_inside_a_list():
    T = TypeVar("T")

    @strawberry.type
    class JsonBlock:
        data: JSON

    @strawberry.type
    class BlockRowType(Generic[T]):
        total: int
        items: List[T]

    @strawberry.type
    class Query:
        @strawberry.field
        def blocks(
            self,
        ) -> List[Union[BlockRowType[int], BlockRowType[str], JsonBlock]]:
            return [
                BlockRowType(total=3, items=["a", "b", "c"]),
                BlockRowType(total=1, items=[1, 2, 3, 4]),
                JsonBlock(data=JSON({"a": 1})),
            ]

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        """query {
        blocks {
            __typename
            ... on IntBlockRowType {
                a: items
            }
            ... on StrBlockRowType {
                b: items
            }
            ... on JsonBlock {
                data
            }
        }
    }"""
    )

    assert not result.errors

    assert result.data == {
        "blocks": [
            {"__typename": "StrBlockRowType", "b": ["a", "b", "c"]},
            {"__typename": "IntBlockRowType", "a": [1, 2, 3, 4]},
            {"__typename": "JsonBlock", "data": {"a": 1}},
        ]
    }


def test_unions_nested_inside_a_list_with_no_items():
    T = TypeVar("T")

    @strawberry.type
    class JsonBlock:
        data: JSON

    @strawberry.type
    class BlockRowType(Generic[T]):
        total: int
        items: List[T]

    @strawberry.type
    class Query:
        @strawberry.field
        def blocks(
            self,
        ) -> List[Union[BlockRowType[int], BlockRowType[str], JsonBlock]]:
            return [
                BlockRowType(total=3, items=[]),
                BlockRowType(total=1, items=[]),
                JsonBlock(data=JSON({"a": 1})),
            ]

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        """query {
        blocks {
            __typename
            ... on IntBlockRowType {
                a: items
            }
            ... on StrBlockRowType {
                b: items
            }
            ... on JsonBlock {
                data
            }
        }
    }"""
    )

    assert not result.errors

    assert result.data == {
        "blocks": [
            {"__typename": "IntBlockRowType", "a": []},
            {"__typename": "IntBlockRowType", "a": []},
            {"__typename": "JsonBlock", "data": {"a": 1}},
        ]
    }


def test_unions_nested_inside_a_list_of_lists():
    T = TypeVar("T")

    @strawberry.type
    class JsonBlock:
        data: JSON

    @strawberry.type
    class BlockRowType(Generic[T]):
        total: int
        items: List[List[T]]

    @strawberry.type
    class Query:
        @strawberry.field
        def blocks(
            self,
        ) -> List[Union[BlockRowType[int], BlockRowType[str], JsonBlock]]:
            return [
                BlockRowType(total=3, items=[["a", "b", "c"]]),
                BlockRowType(total=1, items=[[1, 2, 3, 4]]),
                JsonBlock(data=JSON({"a": 1})),
            ]

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        """query {
        blocks {
            __typename
            ... on IntBlockRowType {
                a: items
            }
            ... on StrBlockRowType {
                b: items
            }
            ... on JsonBlock {
                data
            }
        }
    }"""
    )

    assert not result.errors

    assert result.data == {
        "blocks": [
            {"__typename": "StrBlockRowType", "b": [["a", "b", "c"]]},
            {"__typename": "IntBlockRowType", "a": [[1, 2, 3, 4]]},
            {"__typename": "JsonBlock", "data": {"a": 1}},
        ]
    }


def test_using_generics_with_an_interface():
    T = TypeVar("T")

    @strawberry.interface
    class BlockInterface:
        id: strawberry.ID
        disclaimer: Optional[str] = strawberry.field(default=None)

    @strawberry.type
    class JsonBlock(BlockInterface):
        data: JSON

    @strawberry.type
    class BlockRowType(BlockInterface, Generic[T]):
        total: int
        items: List[T]

    @strawberry.type
    class Query:
        @strawberry.field
        def blocks(self) -> List[BlockInterface]:
            return [
                BlockRowType(id=strawberry.ID("3"), total=3, items=["a", "b", "c"]),
                BlockRowType(id=strawberry.ID("1"), total=1, items=[1, 2, 3, 4]),
                JsonBlock(id=strawberry.ID("2"), data=JSON({"a": 1})),
            ]

    schema = strawberry.Schema(
        query=Query, types=[BlockRowType[int], JsonBlock, BlockRowType[str]]
    )

    expected_schema = textwrap.dedent(
        '''
        interface BlockInterface {
          id: ID!
          disclaimer: String
        }

        type IntBlockRowType implements BlockInterface {
          id: ID!
          disclaimer: String
          total: Int!
          items: [Int!]!
        }

        """
        The `JSON` scalar type represents JSON values as specified by [ECMA-404](https://ecma-international.org/wp-content/uploads/ECMA-404_2nd_edition_december_2017.pdf).
        """
        scalar JSON @specifiedBy(url: "https://ecma-international.org/wp-content/uploads/ECMA-404_2nd_edition_december_2017.pdf")

        type JsonBlock implements BlockInterface {
          id: ID!
          disclaimer: String
          data: JSON!
        }

        type Query {
          blocks: [BlockInterface!]!
        }

        type StrBlockRowType implements BlockInterface {
          id: ID!
          disclaimer: String
          total: Int!
          items: [String!]!
        }
    '''
    ).strip()

    assert str(schema) == expected_schema

    result = schema.execute_sync(
        """query {
        blocks {
            id
            __typename
            ... on IntBlockRowType {
                a: items
            }
            ... on StrBlockRowType {
                b: items
            }
            ... on JsonBlock {
                data
            }
        }
    }"""
    )

    assert not result.errors

    assert result.data == {
        "blocks": [
            {"id": "3", "__typename": "StrBlockRowType", "b": ["a", "b", "c"]},
            {"id": "1", "__typename": "IntBlockRowType", "a": [1, 2, 3, 4]},
            {"id": "2", "__typename": "JsonBlock", "data": {"a": 1}},
        ]
    }


def test_supports_generic_in_unions_with_nesting():
    T = TypeVar("T")

    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Edge(Generic[T]):
        node: T

    @strawberry.type
    class Connection(Generic[T]):
        edge: Edge[T]

    @strawberry.type
    class Fallback:
        node: str

    @strawberry.type
    class Query:
        @strawberry.field
        def users(self) -> Union[Connection[User], Fallback]:
            return Connection(edge=Edge(node=User(name="Patrick")))

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
