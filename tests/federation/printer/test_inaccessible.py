import textwrap
from typing import List

import strawberry


def test_field_inaccessible_printed_correctly():
    @strawberry.federation.interface(inaccessible=True)
    class AnInterface:
        id: strawberry.ID

    @strawberry.interface
    class SomeInterface:
        id: strawberry.ID
        a_field: str = strawberry.federation.field(inaccessible=True)

    @strawberry.federation.type(keys=["upc"], extend=True)
    class Product(SomeInterface):
        upc: str = strawberry.federation.field(external=True, inaccessible=True)

    @strawberry.federation.input(inaccessible=True)
    class AnInput:
        id: strawberry.ID

    @strawberry.federation.type(inaccessible=True)
    class AnInaccessibleType:
        id: strawberry.ID

    @strawberry.federation.type
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> List[Product]:
            return []

    schema = strawberry.federation.Schema(
        query=Query, types=[AnInterface, AnInput, AnInaccessibleType]
    )

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.0", import: ["@external", "@inaccessible", "@key"]) {
          query: Query
        }

        type AnInaccessibleType @inaccessible {
          id: ID!
        }

        input AnInput @inaccessible {
          id: ID!
        }

        interface AnInterface @inaccessible {
          id: ID!
        }

        extend type Product implements SomeInterface @key(fields: "upc") {
          id: ID!
          aField: String! @inaccessible
          upc: String! @external @inaccessible
        }

        type Query {
          _service: _Service!
          _entities(representations: [_Any!]!): [_Entity]!
          topProducts(first: Int!): [Product!]!
        }

        interface SomeInterface {
          id: ID!
          aField: String! @inaccessible
        }

        scalar _Any

        union _Entity = Product

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()
