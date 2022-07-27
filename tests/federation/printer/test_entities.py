# type: ignore

import textwrap
from typing import List

import strawberry


def test_entities_type_when_no_type_has_keys():
    global Review

    @strawberry.federation.type
    class User:
        username: str

    @strawberry.federation.type(extend=True)
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
        directive @external on FIELD_DEFINITION

        extend type Product {
          upc: String! @external
          reviews: [Review!]!
        }

        type Query {
          _service: _Service!
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

        scalar _FieldSet

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()

    del Review


def test_entities_type_when_one_type_has_keys():
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
        directive @external on FIELD_DEFINITION

        directive @key(fields: _FieldSet!, resolvable: Boolean = true) on OBJECT | INTERFACE

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

        scalar _FieldSet

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()

    del Review
