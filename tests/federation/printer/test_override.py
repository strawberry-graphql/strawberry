# type: ignore

import textwrap
from typing import List

import strawberry


def test_field_override_printed_correctly():
    @strawberry.interface
    class SomeInterface:
        id: strawberry.ID

    @strawberry.federation.type(keys=["upc"], extend=True)
    class Product(SomeInterface):
        upc: str = strawberry.federation.field(external=True, override="mySubGraph")

    @strawberry.federation.type
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> List[Product]:
            return []

    schema = strawberry.federation.Schema(query=Query)

    expected = """
        directive @external on FIELD_DEFINITION

        directive @key(fields: _FieldSet!, resolvable: Boolean = true) on OBJECT | INTERFACE

        directive @override(from: String!) on FIELD_DEFINITION

        extend type Product implements SomeInterface @key(fields: "upc") {
          id: ID!
          upc: String! @external @override(from: "mySubGraph")
        }

        type Query {
          _service: _Service!
          _entities(representations: [_Any!]!): [_Entity]!
          topProducts(first: Int!): [Product!]!
        }

        interface SomeInterface {
          id: ID!
        }

        scalar _Any

        union _Entity = Product

        type _Service {
          sdl: String!
        }

        scalar _FieldSet
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()
