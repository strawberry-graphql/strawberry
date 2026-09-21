from decimal import Decimal

from graphql import GraphQLError

import strawberry
from strawberry.utils import IS_GQL_32


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
    expected_message = (
        "Variable '$value' got invalid value 'fail'; Value cannot represent a "
        'Decimal: "fail".'
        if IS_GQL_32
        else "Variable '$value' has invalid value: Value cannot represent a "
        'Decimal: "fail".'
    )
    assert result.errors[0].message == expected_message


def test_parsing_of_non_decimal_value():
    """Test GraphQLError is raised for a value ``Decimal`` cannot parse.
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
        variable_values={"value": True},
    )

    assert result.errors
    assert isinstance(result.errors[0], GraphQLError)
    expected_message = (
        "Variable '$value' got invalid value True; Value cannot represent a "
        'Decimal: "True".'
        if IS_GQL_32
        else "Variable '$value' has invalid value: Value cannot represent a "
        'Decimal: "True".'
    )
    assert result.errors[0].message == expected_message
    original_error = result.errors[0].original_error
    assert isinstance(original_error, GraphQLError)
    assert original_error.original_error is None
