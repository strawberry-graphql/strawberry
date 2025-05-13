import datetime

import pytest
from graphql import GraphQLError

import strawberry
from strawberry.types.execution import ExecutionResult


def test_serialization():
    @strawberry.type
    class Query:
        @strawberry.field
        def serialize(self) -> datetime.time:
            return datetime.time(13, 37)

    schema = strawberry.Schema(Query)

    result = schema.execute_sync("{ serialize }")

    assert not result.errors
    assert result.data["serialize"] == "13:37:00"


def test_deserialization():
    @strawberry.type
    class Query:
        deserialized = None

        @strawberry.field
        def deserialize(self, arg: datetime.time) -> bool:
            Query.deserialized = arg
            return True

    schema = strawberry.Schema(Query)

    query = """query Deserialize($value: Time!) {
        deserialize(arg: $value)
    }"""
    result = schema.execute_sync(query, variable_values={"value": "13:37:00"})

    assert not result.errors
    assert Query.deserialized == datetime.time(13, 37)


def test_deserialization_with_parse_literal():
    @strawberry.type
    class Query:
        deserialized = None

        @strawberry.field
        def deserialize(self, arg: datetime.time) -> bool:
            Query.deserialized = arg
            return True

    schema = strawberry.Schema(Query)

    query = """query Deserialize {
        deserialize(arg: "13:37:00")
    }"""
    result = schema.execute_sync(query)

    assert not result.errors
    assert Query.deserialized == datetime.time(13, 37)


def execute_mutation(value) -> ExecutionResult:
    @strawberry.type
    class Query:
        ok: bool

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def time_input(self, time_input: datetime.time) -> datetime.time:
            assert isinstance(time_input, datetime.time)
            return time_input

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    return schema.execute_sync(
        """
            mutation timeInput($value: Time!) {
                timeInput(timeInput: $value)
            }
        """,
        variable_values={"value": value},
    )


@pytest.mark.parametrize(
    "value",
    [
        "2012-12-01T09:00",
        "03:30+",
        "03:30+1234567",
        "03:30-25:40",
    ],
)
def test_serialization_of_incorrect_time_string(value):
    """Test GraphQLError is raised for incorrect time.
    The error should exclude "original_error".
    """
    result = execute_mutation(value)
    assert result.errors
    assert isinstance(result.errors[0], GraphQLError)


def test_serialization_error_message_for_incorrect_time_string():
    """Test if error message is using original error message
    from time lib, and is properly formatted.
    """
    result = execute_mutation("25:00")
    assert result.errors
    assert result.errors[0].message == (
        "Variable '$value' got invalid value '25:00'; Value cannot represent a "
        'Time: "25:00". hour must be in 0..23'
    )
