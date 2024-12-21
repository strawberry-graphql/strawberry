# type: ignore

import textwrap

import strawberry
from strawberry.schema.config import StrawberryConfig


def test_field_provides_are_printed_correctly_camel_case_on():
    global Review

    @strawberry.federation.type
    class User:
        username: str

    @strawberry.federation.type(keys=["upc"], extend=True)
    class Product:
        upc: str = strawberry.federation.field(external=True)
        the_name: str = strawberry.federation.field(external=True)
        reviews: list["Review"]

    @strawberry.federation.type
    class Review:
        body: str
        author: User
        product: Product = strawberry.federation.field(provides=["name"])

    @strawberry.federation.type
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> list[Product]:  # pragma: no cover
            return []

    schema = strawberry.federation.Schema(
        query=Query,
        config=StrawberryConfig(auto_camel_case=True),
        enable_federation_2=True,
    )

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@external", "@key", "@provides"]) {
          query: Query
        }

        extend type Product @key(fields: "upc") {
          upc: String! @external
          theName: String! @external
          reviews: [Review!]!
        }

        type Query {
          _entities(representations: [_Any!]!): [_Entity]!
          _service: _Service!
          topProducts(first: Int!): [Product!]!
        }

        type Review {
          body: String!
          author: User!
          product: Product! @provides(fields: "name")
        }

        type User {
          username: String!
        }

        scalar _Any

        union _Entity = Product

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()

    del Review


def test_field_provides_are_printed_correctly_camel_case_off():
    global Review

    @strawberry.federation.type
    class User:
        username: str

    @strawberry.federation.type(keys=["upc"], extend=True)
    class Product:
        upc: str = strawberry.federation.field(external=True)
        the_name: str = strawberry.federation.field(external=True)
        reviews: list["Review"]

    @strawberry.federation.type
    class Review:
        body: str
        author: User
        product: Product = strawberry.federation.field(provides=["name"])

    @strawberry.federation.type
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> list[Product]:  # pragma: no cover
            return []

    schema = strawberry.federation.Schema(
        query=Query,
        config=StrawberryConfig(auto_camel_case=False),
        enable_federation_2=True,
    )

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@external", "@key", "@provides"]) {
          query: Query
        }

        extend type Product @key(fields: "upc") {
          upc: String! @external
          the_name: String! @external
          reviews: [Review!]!
        }

        type Query {
          _entities(representations: [_Any!]!): [_Entity]!
          _service: _Service!
          top_products(first: Int!): [Product!]!
        }

        type Review {
          body: String!
          author: User!
          product: Product! @provides(fields: "name")
        }

        type User {
          username: String!
        }

        scalar _Any

        union _Entity = Product

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()

    del Review
