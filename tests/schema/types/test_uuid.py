import uuid

from graphql import GraphQLError

import strawberry


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
    assert result.errors[0].message == (
        "Variable '$value' got invalid value 'fail'; Value cannot represent a "
        'UUID: "fail". badly formed hexadecimal UUID string'
    )
