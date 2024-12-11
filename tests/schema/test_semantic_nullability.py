import textwrap
from typing import List, Optional, Required

import strawberry
from strawberry.schema.config import StrawberryConfig


def test_entities_type_when_no_type_has_keys():
    @strawberry.type()
    class Product:
        upc: str
        name: str
        price: Required[int]
        weight: Optional[int]

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> List[Product]:
            return []

    schema = strawberry.Schema(
        query=Query, config=StrawberryConfig(semantic_nullability_beta=True)
    )

    expected_sdl = textwrap.dedent("""
        type Product {
          upc: String!
          name: String
          price: Int
          weight: Int
        }

        extend type Query {
          _service: _Service!
          topProducts(first: Int!): [Product!]!
        }

        scalar _Any

        type _Service {
          sdl: String!
        }
    """).strip()

    assert str(schema) == expected_sdl

    query = """
        query {
            __type(name: "_Entity") {
                kind
                possibleTypes {
                    name
                }
            }
        }
    """

    result = schema.execute_sync(query)

    assert not result.errors

    assert result.data == {"__type": None}
