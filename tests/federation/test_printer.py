# type: ignore

import textwrap
from typing import List

import strawberry


def test_entities_type_when_no_type_has_keys():
    global Review

    @strawberry.federation.type
    class User:
        username: str

    @strawberry.federation.type(keys=["upc"], extend=True)
    class Product:
        upc: str = strawberry.federation.field(external=True)
        reviews: List["Review"]

    @strawberry.federation.type
    class Review:
        body: str
        author: User
        product: Product

    @strawberry.federation.type
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> List[Product]:
            return []

    schema = strawberry.federation.Schema(query=Query)

    expected = """
        extend type Product @key(fields: "upc") {
          upc: String! @external
          reviews: [Review!]!
        }

        type Query {
          _service: _Service!
          _entities(representations: [_Any!]!): [_Entity]!
          topProducts(first: Int!): [Product!]!
        }

        type Review {
          body: String!
          author: User!
          product: Product!
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


def test_fields_requires_are_printed_correctly():
    global Review

    @strawberry.federation.type
    class User:
        username: str

    @strawberry.federation.type(keys=["upc"], extend=True)
    class Product:
        upc: str = strawberry.federation.field(external=True)
        field1: str = strawberry.federation.field(external=True)
        field2: str = strawberry.federation.field(external=True)
        field3: str = strawberry.federation.field(external=True)

        @strawberry.federation.field(requires=["field1", "field2", "field3"])
        def reviews(self) -> List["Review"]:
            return []

    @strawberry.federation.type
    class Review:
        body: str
        author: User
        product: Product

    @strawberry.federation.type
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> List[Product]:
            return []

    schema = strawberry.federation.Schema(query=Query)

    expected = """
        extend type Product @key(fields: "upc") {
          upc: String! @external
          field1: String! @external
          field2: String! @external
          field3: String! @external
          reviews: [Review!]! @requires(fields: "field1 field2 field3")
        }

        type Query {
          _service: _Service!
          _entities(representations: [_Any!]!): [_Entity]!
          topProducts(first: Int!): [Product!]!
        }

        type Review {
          body: String!
          author: User!
          product: Product!
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
