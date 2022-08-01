# type: ignore

import textwrap
from typing import List

import strawberry


def test_field_shareable_printed_correctly():
    @strawberry.interface
    class SomeInterface:
        id: strawberry.ID

    @strawberry.federation.type(keys=["upc"], extend=True, shareable=True)
    class Product(SomeInterface):
        upc: str = strawberry.federation.field(external=True, shareable=True)

    @strawberry.federation.type
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> List[Product]:
            return []

    schema = strawberry.federation.Schema(query=Query)

    expected = """
        directive @external on FIELD_DEFINITION

        directive @key(fields: _FieldSet!, resolvable: Boolean = true) on OBJECT | INTERFACE

        directive @shareable on FIELD_DEFINITION | OBJECT

        extend type Product implements SomeInterface @key(fields: "upc") @shareable {
          id: ID!
          upc: String! @external @shareable
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
