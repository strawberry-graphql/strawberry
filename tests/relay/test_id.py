from __future__ import annotations

from inline_snapshot import snapshot

import strawberry
from strawberry.relay import GlobalID
from strawberry.schema.config import StrawberryConfig


@strawberry.type
class Book:
    id: GlobalID
    title: str
    debug: str


@strawberry.type
class Query:
    @strawberry.field
    def books(self) -> list[Book]:
        return []

    @strawberry.field
    def book(self, id: GlobalID) -> Book | None:
        return Book(id=id, title="Title", debug=str(type(id)))


def test_uses_id_by_default() -> None:
    schema = strawberry.Schema(query=Query)

    assert str(schema) == snapshot("""\
type Book {
  id: ID!
  title: String!
  debug: String!
}

type Query {
  books: [Book!]!
  book(id: ID!): Book
}\
""")

    result = schema.execute_sync('query { book(id: "Qm9vazox") { id, debug } }')

    assert result.errors is None
    assert result.data == snapshot(
        {
            "book": {
                "id": "Qm9vazox",
                "debug": "<class 'strawberry.relay.types.GlobalID'>",
            }
        }
    )


def test_we_can_still_use_global_id() -> None:
    schema = strawberry.Schema(
        query=Query, config=StrawberryConfig(relay_use_legacy_global_id=True)
    )

    assert str(schema) == snapshot('''\
type Book {
  id: GlobalID!
  title: String!
  debug: String!
}

"""
The `ID` scalar type represents a unique identifier, often used to refetch an object or as key for a cache. The ID type appears in a JSON response as a String; however, it is not intended to be human-readable. When expected as an input type, any string (such as `"4"`) or integer (such as `4`) input value will be accepted as an ID.
"""
scalar GlobalID @specifiedBy(url: "https://relay.dev/graphql/objectidentification.htm")

type Query {
  books: [Book!]!
  book(id: GlobalID!): Book
}\
''')

    result = schema.execute_sync('query { book(id: "Qm9vazox") { id, debug } }')

    assert result.errors is None
    assert result.data == snapshot(
        {
            "book": {
                "id": "Qm9vazox",
                "debug": "<class 'strawberry.relay.types.GlobalID'>",
            }
        }
    )


def test_can_use_both_global_id_and_id() -> None:
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, id: GlobalID) -> str:
            return "Hello World"

        @strawberry.field
        def hello2(self, id: strawberry.ID) -> str:
            return "Hello World"

    schema = strawberry.Schema(Query)

    assert str(schema) == snapshot("""\
type Query {
  hello(id: ID!): String!
  hello2(id: ID!): String!
}\
""")


def test_can_use_both_global_id_and_id_legacy() -> None:
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, id: GlobalID) -> str:
            return "Hello World"

        @strawberry.field
        def hello2(self, id: strawberry.ID) -> str:
            return "Hello World"

    schema = strawberry.Schema(
        query=Query, config=StrawberryConfig(relay_use_legacy_global_id=True)
    )

    assert str(schema) == snapshot('''\
"""
The `ID` scalar type represents a unique identifier, often used to refetch an object or as key for a cache. The ID type appears in a JSON response as a String; however, it is not intended to be human-readable. When expected as an input type, any string (such as `"4"`) or integer (such as `4`) input value will be accepted as an ID.
"""
scalar GlobalID @specifiedBy(url: "https://relay.dev/graphql/objectidentification.htm")

type Query {
  hello(id: GlobalID!): String!
  hello2(id: ID!): String!
}\
''')
