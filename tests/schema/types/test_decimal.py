from decimal import Decimal

from graphql import GraphQLError

import strawberry


def test_decimal():
    @strawberry.type
    class Query:
        @strawberry.field
        def example_decimal(self) -> Decimal:
            return Decimal("3.14159")

    schema = strawberry.Schema(Query)

    result = schema.execute_sync("{ exampleDecimal }")

    assert not result.errors
    assert result.data["exampleDecimal"] == "3.14159"


def test_decimal_as_input():
    @strawberry.type
    class Query:
        @strawberry.field
        def example_decimal(self, decimal: Decimal) -> Decimal:
            return decimal

    schema = strawberry.Schema(Query)

    result = schema.execute_sync('{ exampleDecimal(decimal: "3.14") }')

    assert not result.errors
    assert result.data["exampleDecimal"] == "3.14"


def test_serialization_of_incorrect_decimal_string():
    """Test GraphQLError is raised for an invalid Decimal.
    The error should exclude "original_error".
    """

    @strawberry.type
    class Query:
        ok: bool

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def decimal_input(self, decimal_input: Decimal) -> Decimal:
            return decimal_input

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    result = schema.execute_sync(
        """
            mutation decimalInput($value: Decimal!) {
                decimalInput(decimalInput: $value)
            }
        """,
        variable_values={"value": "fail"},
    )

    assert result.errors
    assert isinstance(result.errors[0], GraphQLError)
    assert result.errors[0].message == (
        "Variable '$value' got invalid value 'fail'; Value cannot represent a "
        'Decimal: "fail".'
    )
