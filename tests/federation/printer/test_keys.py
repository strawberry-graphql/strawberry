# type: ignore

import textwrap
from typing import List

import strawberry
from strawberry.federation.schema_directives import Key


def test_multiple_keys():
    # also confirm that the "resolvable: True" works
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

    schema = strawberry.federation.Schema(query=Query)

    expected = """
        directive @external on FIELD_DEFINITION

        directive @key(fields: _FieldSet!, resolvable: Boolean = true) on OBJECT | INTERFACE

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

        scalar _FieldSet

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()

    del Review
