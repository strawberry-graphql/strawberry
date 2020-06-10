from decimal import Decimal

import strawberry
from graphql import graphql_sync


def test_decimal():
    @strawberry.type
    class Query:
        @strawberry.field
        def example_decimal(self) -> Decimal:
            return Decimal("3.14159")

    schema = strawberry.Schema(Query)

    result = graphql_sync(schema, "{ exampleDecimal }")

    assert not result.errors
    assert result.data["exampleDecimal"] == "3.14159"


def test_decimal_as_input():
    @strawberry.type
    class Query:
        @strawberry.field
        def example_decimal(self, decimal: Decimal) -> Decimal:
            return decimal

    schema = strawberry.Schema(Query)

    result = graphql_sync(schema, '{ exampleDecimal(decimal: "3.14") }')

    assert not result.errors
    assert result.data["exampleDecimal"] == "3.14"
