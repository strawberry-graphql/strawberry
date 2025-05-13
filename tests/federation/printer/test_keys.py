# type: ignore

import textwrap

import strawberry
from strawberry.federation.schema_directives import Key


def test_keys_federation_1():
    global Review

    @strawberry.federation.type
    class User:
        username: str

    @strawberry.federation.type(keys=[Key(fields="upc", resolvable=True)], extend=True)
    class Product:
        upc: str = strawberry.federation.field(external=True)
        reviews: list["Review"]

    @strawberry.federation.type(keys=["body"])
    class Review:
        body: str
        author: User
        product: Product

    @strawberry.federation.type
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> list[Product]:  # pragma: no cover
            return []

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=False)

    expected = """
        extend type Product @key(fields: "upc") {
          upc: String! @external
          reviews: [Review!]!
        }

        type Query {
          _entities(representations: [_Any!]!): [_Entity]!
          _service: _Service!
          topProducts(first: Int!): [Product!]!
        }

        type Review @key(fields: "body") {
          body: String!
          author: User!
          product: Product!
        }

        type User {
          username: String!
        }

        scalar _Any

        union _Entity = Product | Review

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()

    del Review


def test_keys_federation_2():
    global Review

    @strawberry.federation.type
    class User:
        username: str

    @strawberry.federation.type(keys=[Key(fields="upc", resolvable=True)], extend=True)
    class Product:
        upc: str = strawberry.federation.field(external=True)
        reviews: list["Review"]

    @strawberry.federation.type(keys=["body"])
    class Review:
        body: str
        author: User
        product: Product

    @strawberry.federation.type
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> list[Product]:  # pragma: no cover
            return []

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@external", "@key"]) {
          query: Query
        }

        extend type Product @key(fields: "upc", resolvable: true) {
          upc: String! @external
          reviews: [Review!]!
        }

        type Query {
          _entities(representations: [_Any!]!): [_Entity]!
          _service: _Service!
          topProducts(first: Int!): [Product!]!
        }

        type Review @key(fields: "body") {
          body: String!
          author: User!
          product: Product!
        }

        type User {
          username: String!
        }

        scalar _Any

        union _Entity = Product | Review

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()

    del Review
