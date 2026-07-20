import uuid

import pytest
from graphql import GraphQLError

import strawberry
from strawberry.utils import IS_GQL_32


def test_uuid():
    @strawberry.type
    class Query:
        @strawberry.field
        def example_uuid_out(self) -> uuid.UUID:
            return uuid.NAMESPACE_DNS

    schema = strawberry.Schema(Query)

    result = schema.execute_sync("{ exampleUuidOut }")

    assert not result.errors
    assert result.data["exampleUuidOut"] == str(uuid.NAMESPACE_DNS)


def test_uuid_as_input():
    @strawberry.type
    class Query:
        @strawberry.field
        def example_uuid_in(self, uid: uuid.UUID) -> uuid.UUID:
            return uid

    schema = strawberry.Schema(Query)

    result = schema.execute_sync(f'{{ exampleUuidIn(uid: "{uuid.NAMESPACE_DNS!s}") }}')

    assert not result.errors
    assert result.data["exampleUuidIn"] == str(uuid.NAMESPACE_DNS)


def test_serialization_of_incorrect_uuid_string():
    """Test GraphQLError is raised for an invalid UUID.
    The error should exclude "original_error".
    """

    @strawberry.type
    class Query:
        ok: bool

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def uuid_input(self, uuid_input: uuid.UUID) -> uuid.UUID:
            return uuid_input

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    result = schema.execute_sync(
        """
            mutation uuidInput($value: UUID!) {
                uuidInput(uuidInput: $value)
            }
        """,
        variable_values={"value": "fail"},
    )

    assert result.errors
    assert isinstance(result.errors[0], GraphQLError)
    expected_message = (
        "Variable '$value' got invalid value 'fail'; Value cannot represent a "
        'UUID: "fail". badly formed hexadecimal UUID string'
        if IS_GQL_32
        else "Variable '$value' has invalid value: Value cannot represent a "
        'UUID: "fail". badly formed hexadecimal UUID string'
    )
    assert result.errors[0].message == expected_message


@pytest.mark.parametrize(
    "value",
    [
        469610.0,
        # would stringify into 32 valid hexadecimal characters, so it must be
        # rejected by type, not by parsing
        10000000000000000000000000000000,
        True,
    ],
)
def test_parsing_of_non_string_value(value):
    """Test GraphQLError is raised for a non-string value.
    The parser must not leak an AttributeError from ``uuid.UUID``, and the
    string form of the value must not be accepted either.
    """

    @strawberry.type
    class Query:
        ok: bool

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def uuid_input(self, uuid_input: uuid.UUID) -> uuid.UUID:
            return uuid_input

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    result = schema.execute_sync(
        """
            mutation uuidInput($value: UUID!) {
                uuidInput(uuidInput: $value)
            }
        """,
        variable_values={"value": value},
    )

    assert result.errors
    error = result.errors[0]
    assert isinstance(error, GraphQLError)
    assert (
        f'Value cannot represent a UUID: "{value}". Expected a string.' in error.message
    )
    assert isinstance(error.original_error, GraphQLError)
    assert error.original_error.original_error is None
