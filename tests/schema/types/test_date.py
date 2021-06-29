import datetime

import pytest

from graphql import GraphQLError

import strawberry


@pytest.mark.parametrize(
    "typing,instance,serialized",
    [
        (datetime.date, datetime.date(2019, 10, 25), "2019-10-25"),
    ],
)
def test_serialization(typing, instance, serialized):
    @strawberry.type
    class Query:
        @strawberry.field
        def serialize(self) -> typing:
            return instance

    schema = strawberry.Schema(Query)

    result = schema.execute_sync("{ serialize }")

    assert not result.errors
    assert result.data["serialize"] == serialized


@pytest.mark.parametrize(
    "typing,name,instance,serialized",
    [
        (datetime.date, "Date", datetime.date(2019, 10, 25), "2019-10-25"),
    ],
)
def test_deserialization(typing, name, instance, serialized):
    @strawberry.type
    class Query:
        deserialized = None

        @strawberry.field
        def deserialize(self, arg: typing) -> bool:
            Query.deserialized = arg
            return True

    schema = strawberry.Schema(Query)

    query = f"""query Deserialize($value: {name}!) {{
        deserialize(arg: $value)
    }}"""
    result = schema.execute_sync(query, variable_values={"value": serialized})

    assert not result.errors
    assert Query.deserialized == instance


@pytest.mark.parametrize(
    "typing,instance,serialized",
    [
        (datetime.date, datetime.date(2019, 10, 25), "2019-10-25"),
    ],
)
def test_deserialization_with_parse_literal(typing, instance, serialized):
    @strawberry.type
    class Query:
        deserialized = None

        @strawberry.field
        def deserialize(self, arg: typing) -> bool:
            Query.deserialized = arg
            return True

    schema = strawberry.Schema(Query)

    query = f"""query Deserialize {{
        deserialize(arg: "{serialized}")
    }}"""
    result = schema.execute_sync(query)

    assert not result.errors
    assert Query.deserialized == instance


def execute_mutation(value):
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
        f"""
            mutation {{
                dateInput(dateInput: "{value}")
            }}
        """
    )


@pytest.mark.parametrize(
    "value",
    (
        "2012-12-01T09:00",
        "2012-13-01",
        "2012-04-9",
        "20120411",
    ),
)
def test_serialization_of_incorrect_date_string(value):
    """
    Test GraphQLError is raised for incorrect date.
    The error should exclude "original_error".
    """

    result = execute_mutation(value)
    assert result.errors
    assert isinstance(result.errors[0], GraphQLError)
    assert result.errors[0].original_error is None


def test_serialization_error_message_for_incorrect_date_string():
    """
    Test if error message is using original error message from date lib, and is properly formatted
    """

    result = execute_mutation("2021-13-01")
    assert result.errors
    assert result.errors[0].message == (
        'Value cannot represent a Date: "2021-13-01". month must be in 1..12'
    )
