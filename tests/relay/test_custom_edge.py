import textwrap
from typing import Any
from typing_extensions import Self

import pytest

import strawberry
from strawberry import Schema, relay
from strawberry.relay import NodeType, to_base64


@pytest.fixture
def schema() -> Schema:
    @strawberry.type
    class Fruit(relay.Node):
        code: relay.NodeID[int]

    @strawberry.type(name="Edge", description="An edge in a connection.")
    class CustomEdge(relay.Edge[NodeType]):
        CURSOR_PREFIX = "customprefix"
        index: int

        @classmethod
        def resolve_edge(
            cls, node: NodeType, *, cursor: Any = None, **kwargs: Any
        ) -> Self:
            assert isinstance(cursor, int)
            return super().resolve_edge(node, cursor=cursor, index=cursor, **kwargs)

    @strawberry.type(name="Connection", description="A connection to a list of items.")
    class CustomListConnection(relay.ListConnection[NodeType]):
        edges: list[CustomEdge[NodeType]] = strawberry.field(
            description="Contains the nodes in this connection"
        )

    @strawberry.type
    class Query:
        @relay.connection(CustomListConnection[Fruit])
        def fruits(self) -> list[Fruit]:
            return [Fruit(code=i) for i in range(10)]

    return strawberry.Schema(query=Query)


def test_schema_with_custom_edge_class(schema: Schema):
    expected = textwrap.dedent(
        '''
        type Fruit implements Node {
          """The Globally Unique ID of this object"""
          id: GlobalID!
        }

        """A connection to a list of items."""
        type FruitConnection {
          """Pagination data for this connection"""
          pageInfo: PageInfo!

          """Contains the nodes in this connection"""
          edges: [FruitEdge!]!
        }

        """An edge in a connection."""
        type FruitEdge {
          """A cursor for use in pagination"""
          cursor: String!

          """The item at the end of the edge"""
          node: Fruit!
          index: Int!
        }

        """
        The `ID` scalar type represents a unique identifier, often used to refetch an object or as key for a cache. The ID type appears in a JSON response as a String; however, it is not intended to be human-readable. When expected as an input type, any string (such as `"4"`) or integer (such as `4`) input value will be accepted as an ID.
        """
        scalar GlobalID @specifiedBy(url: "https://relay.dev/graphql/objectidentification.htm")

        """An object with a Globally Unique ID"""
        interface Node {
          """The Globally Unique ID of this object"""
          id: GlobalID!
        }

        """Information to aid in pagination."""
        type PageInfo {
          """When paginating forwards, are there more items?"""
          hasNextPage: Boolean!

          """When paginating backwards, are there more items?"""
          hasPreviousPage: Boolean!

          """When paginating backwards, the cursor to continue."""
          startCursor: String

          """When paginating forwards, the cursor to continue."""
          endCursor: String
        }

        type Query {
          fruits(
            """Returns the items in the list that come before the specified cursor."""
            before: String = null

            """Returns the items in the list that come after the specified cursor."""
            after: String = null

            """Returns the first n items from the list."""
            first: Int = null

            """Returns the items in the list that come after the specified cursor."""
            last: Int = null
          ): FruitConnection!
        }
        '''
    ).strip()
    assert str(schema) == expected


def test_custom_cursor_prefix_used(schema: Schema):
    result = schema.execute_sync(
        """
        query {
          fruits {
            edges {
              cursor
              node {
                id
              }
            }
          }
        }
        """
    )
    assert result.errors is None
    assert result.data == {
        "fruits": {
            "edges": [
                {
                    "cursor": to_base64("customprefix", i),
                    "node": {"id": to_base64("Fruit", i)},
                }
                for i in range(10)
            ]
        }
    }


def test_custom_cursor_prefix_can_be_parsed(schema: Schema):
    result = schema.execute_sync(
        """
        query TestQuery($after: String) {
          fruits(after: $after) {
            edges {
              cursor
              node {
                id
              }
            }
          }
        }
        """,
        {"after": to_base64("customprefix", 2)},
    )
    assert result.errors is None
    assert result.data == {
        "fruits": {
            "edges": [
                {
                    "cursor": to_base64("customprefix", i),
                    "node": {"id": to_base64("Fruit", i)},
                }
                for i in range(3, 10)
            ]
        }
    }


def test_custom_edge_class_fields_can_be_resolved(schema: Schema):
    result = schema.execute_sync(
        """
        query TestQuery($after: String) {
          fruits(after: $after) {
            edges {
              index
              node {
                id
              }
            }
          }
        }
        """,
        {"after": to_base64("customprefix", 2)},
    )
    assert result.errors is None
    assert result.data == {
        "fruits": {
            "edges": [
                {"index": i, "node": {"id": to_base64("Fruit", i)}}
                for i in range(3, 10)
            ]
        }
    }
