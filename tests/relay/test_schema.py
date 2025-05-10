import pathlib
import textwrap

from pytest_snapshot.plugin import Snapshot

import strawberry
from strawberry import relay
from strawberry.relay.utils import to_base64

from .schema import schema
from .schema_future_annotations import schema as schema_future_annotations

SNAPSHOTS_DIR = pathlib.Path(__file__).parent / "snapshots"


def test_schema(snapshot: Snapshot):
    snapshot.snapshot_dir = SNAPSHOTS_DIR
    snapshot.assert_match(str(schema), "schema.gql")


def test_schema_future_annotations(snapshot: Snapshot):
    snapshot.snapshot_dir = SNAPSHOTS_DIR
    snapshot.assert_match(
        str(schema_future_annotations),
        "schema_future_annotations.gql",
    )


def test_node_id_annotation():
    @strawberry.type
    class Fruit(relay.Node):
        code: relay.NodeID[int]

    @strawberry.type
    class Query:
        @relay.connection(relay.ListConnection[Fruit])
        def fruits(self) -> list[Fruit]:
            return [Fruit(code=i) for i in range(10)]

    schema = strawberry.Schema(query=Query)
    expected = textwrap.dedent(
        '''
        type Fruit implements Node {
          """The Globally Unique ID of this object"""
          id: ID!
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
        }

        """An object with a Globally Unique ID"""
        interface Node {
          """The Globally Unique ID of this object"""
          id: ID!
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
    result = schema.execute_sync(
        """
        query {
          fruits {
            edges {
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
            "edges": [{"node": {"id": to_base64("Fruit", i)}} for i in range(10)]
        }
    }


def test_node_id_annotation_in_superclass():
    @strawberry.type
    class BaseFruit(relay.Node):
        code: relay.NodeID[int]

    @strawberry.type
    class Fruit(BaseFruit): ...

    @strawberry.type
    class Query:
        @relay.connection(relay.ListConnection[Fruit])
        def fruits(self) -> list[Fruit]:
            return [Fruit(code=i) for i in range(10)]

    schema = strawberry.Schema(query=Query)
    expected = textwrap.dedent(
        '''
        type Fruit implements Node {
          """The Globally Unique ID of this object"""
          id: ID!
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
        }

        """An object with a Globally Unique ID"""
        interface Node {
          """The Globally Unique ID of this object"""
          id: ID!
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
    result = schema.execute_sync(
        """
        query {
          fruits {
            edges {
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
            "edges": [{"node": {"id": to_base64("Fruit", i)}} for i in range(10)]
        }
    }


def test_node_id_annotation_in_superclass_and_subclass():
    @strawberry.type
    class BaseFruit(relay.Node):
        code: relay.NodeID[int]

    @strawberry.type
    class Fruit(BaseFruit):
        other_code: relay.NodeID[int]

    @strawberry.type
    class Query:
        @relay.connection(relay.ListConnection[Fruit])
        def fruits(self) -> list[Fruit]:
            return [Fruit(code=i, other_code=i) for i in range(10)]

    schema = strawberry.Schema(query=Query)
    expected = textwrap.dedent(
        '''
        type Fruit implements Node {
          """The Globally Unique ID of this object"""
          id: ID!
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
        }

        """An object with a Globally Unique ID"""
        interface Node {
          """The Globally Unique ID of this object"""
          id: ID!
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
    result = schema.execute_sync(
        """
        query {
          fruits {
            edges {
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
            "edges": [{"node": {"id": to_base64("Fruit", i)}} for i in range(10)]
        }
    }


def test_overwrite_resolve_id_and_no_node_id():
    @strawberry.type
    class Fruit(relay.Node):
        color: str

        @classmethod
        def resolve_id(cls, root) -> str:
            return "test"  # pragma: no cover

    @strawberry.type
    class Query:
        fruit: Fruit

    expected_type = textwrap.dedent(
        '''
          type Fruit implements Node {
          """The Globally Unique ID of this object"""
          id: ID!
          color: String!
        }

        """An object with a Globally Unique ID"""
        interface Node {
          """The Globally Unique ID of this object"""
          id: ID!
        }

        type Query {
          fruit: Fruit!
        }
        '''
    )

    schema = strawberry.Schema(query=Query)

    assert str(schema) == textwrap.dedent(expected_type).strip()
