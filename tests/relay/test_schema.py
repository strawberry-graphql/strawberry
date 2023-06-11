import pathlib
import textwrap
from typing import List

import strawberry
from strawberry import relay
from strawberry.relay.utils import to_base64

from .schema import schema


def test_schema():
    schema_output = str(schema).strip("\n").strip(" ")
    output = pathlib.Path(__file__).parent / "schema.gql"
    if not output.exists():
        with output.open("w") as f:
            f.write(schema_output + "\n")

    with output.open() as f:
        expected = f.read().strip("\n").strip(" ")

    assert schema_output == expected


def test_node_id_annotation():
    @strawberry.type
    class Fruit(relay.Node):
        code: relay.NodeID[int]

    @strawberry.type
    class Query:
        @relay.connection(relay.ListConnection[Fruit])
        def fruits(self) -> List[Fruit]:
            return [Fruit(code=i) for i in range(10)]

    schema = strawberry.Schema(query=Query)
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
    class Fruit(BaseFruit):
        ...

    @strawberry.type
    class Query:
        @relay.connection(relay.ListConnection[Fruit])
        def fruits(self) -> List[Fruit]:
            return [Fruit(code=i) for i in range(10)]

    schema = strawberry.Schema(query=Query)
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
        def fruits(self) -> List[Fruit]:
            return [Fruit(code=i, other_code=i) for i in range(10)]

    schema = strawberry.Schema(query=Query)
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
