import datetime

import pytest
from graphql import GraphQLError

import strawberry
from strawberry.types.execution import ExecutionResult


def test_serialization():
    @strawberry.type
    class Query:
        @strawberry.field
        def serialize(self) -> datetime.date:
            return datetime.date(2019, 10, 25)

    schema = strawberry.Schema(Query)

    result = schema.execute_sync("{ serialize }")

    assert not result.errors
    assert result.data["serialize"] == "2019-10-25"


def test_deserialization():
    @strawberry.type
    class Query:
        deserialized = None

        @strawberry.field
        def deserialize(self, arg: datetime.date) -> bool:
            Query.deserialized = arg
            return True

    schema = strawberry.Schema(Query)

    query = """query Deserialize($value: Date!) {
        deserialize(arg: $value)
    }"""
    result = schema.execute_sync(query, variable_values={"value": "2019-10-25"})

    assert not result.errors
    assert Query.deserialized == datetime.date(2019, 10, 25)


def test_deserialization_with_parse_literal():
    @strawberry.type
    class Query:
        deserialized = None

        @strawberry.field
        def deserialize(self, arg: datetime.date) -> bool:
            Query.deserialized = arg
            return True

    schema = strawberry.Schema(Query)

    query = """query Deserialize {
        deserialize(arg: "2019-10-25")
    }"""
    result = schema.execute_sync(query)

    assert not result.errors
    assert Query.deserialized == datetime.date(2019, 10, 25)


def execute_mutation(value) -> ExecutionResult:
    @strawberry.type
    class Query:
        ok: bool

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def date_input(self, date_input: datetime.date) -> datetime.date:
            assert isinstance(date_input, datetime.date)
            return date_input

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    return schema.execute_sync(
        """
            mutation dateInput($value: Date!) {
                dateInput(dateInput: $value)
            }
        """,
        variable_values={"value": value},
    )


@pytest.mark.parametrize(
    "value",
    [
        "2012-12-01T09:00",
        "2012-13-01",
        "2012-04-9",
        #  this might have been fixed in 3.11
        # "20120411",
    ],
)
def test_serialization_of_incorrect_date_string(value):
    """Test GraphQLError is raised for incorrect date.
    The error should exclude "original_error".
    """
    result = execute_mutation(value)
    assert result.errors
    assert isinstance(result.errors[0], GraphQLError)


def test_serialization_error_message_for_incorrect_date_string():
    """Test if error message is using original error message from
    date lib, and is properly formatted.
    """
    result = execute_mutation("2021-13-01")
    assert result.errors
    assert result.errors[0].message == (
        "Variable '$value' got invalid value '2021-13-01'; Value cannot represent a "
        'Date: "2021-13-01". month must be in 1..12'
    )
