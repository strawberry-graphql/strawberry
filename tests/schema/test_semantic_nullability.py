import textwrap
from typing import List, Optional

import pytest

import strawberry
from strawberry.exceptions.semantic_nullability import InvalidNullReturnError
from strawberry.schema.config import StrawberryConfig
from strawberry.types.strict_non_null import NonNull


def test_semantic_nullability_enabled():
    @strawberry.type
    class Product:
        upc: str
        name: str
        price: NonNull[int]
        weight: Optional[int]

    @strawberry.type
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> List[Product]:
            return []

    schema = strawberry.Schema(
        query=Query, config=StrawberryConfig(semantic_nullability_beta=True)
    )

    expected_sdl = textwrap.dedent("""
        directive @semanticNonNull(level: Int = null) on FIELD_DEFINITION | OBJECT | INTERFACE | SCALAR | ENUM

        type Product {
          upc: String @semanticNonNull(level: null)
          name: String @semanticNonNull(level: null)
          price: Int!
          weight: Int @semanticNonNull(level: null)
        }

        type Query {
          topProducts(first: Int): [Product] @semanticNonNull(level: null)
        }
    """).strip()

    assert str(schema) == expected_sdl


def test_semantic_nullability_error_on_null():
    @strawberry.type
    class Query:
        @strawberry.field
        def greeting(self) -> str:
            return None

    schema = strawberry.Schema(
        query=Query, config=StrawberryConfig(semantic_nullability_beta=True)
    )

    with pytest.raises(InvalidNullReturnError):
        result = schema.execute_sync("{ greeting }")
