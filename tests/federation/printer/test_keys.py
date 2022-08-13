# type: ignore

import textwrap
from typing import List

import strawberry
from strawberry.federation.schema_directives import Key
from strawberry.schema.config import StrawberryConfig


def test_keys():
    global Review

    @strawberry.federation.type
    class User:
        username: str

    @strawberry.federation.type(keys=[Key("upc", True)], extend=True)
    class Product:
        upc: str = strawberry.federation.field(external=True)
        reviews: List["Review"]

    @strawberry.federation.type(keys=["body"])
    class Review:
        body: str
        author: User
        product: Product

    @strawberry.federation.type
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> List[Product]:
            return []

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.0", import: ["@external", "@key"]) {
          query: Query
        }

        extend type Product @key(fields: "upc", resolvable: true) {
          upc: String! @external
          reviews: [Review!]!
        }

        type Query {
          _service: _Service!
          _entities(representations: [_Any!]!): [_Entity]!
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


def test_keys_respects_camel_casing():
    global Review

    @strawberry.federation.type(keys=["the_upc"])
    class Product:
        the_upc: str

    @strawberry.federation.type
    class Query:
        top_products: List[Product]

    schema = strawberry.federation.Schema(
        query=Query,
        enable_federation_2=True,
        config=StrawberryConfig(auto_camel_case=True),
    )

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.0", import: ["@key"]) {
          query: Query
        }

        type Product @key(fields: "theUpc") {
          theUpc: String!
        }

        type Query {
          _service: _Service!
          _entities(representations: [_Any!]!): [_Entity]!
          topProducts: [Product!]!
        }

        scalar _Any

        union _Entity = Product

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()

    del Review
