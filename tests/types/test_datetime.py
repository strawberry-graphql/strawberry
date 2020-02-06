import datetime

import pytest

import strawberry
from graphql import graphql_sync
from strawberry.types.datetime import Date, DateTime, Time


@pytest.mark.parametrize(
    "typing,instance,serialized",
    [
        (Date, datetime.date(2019, 10, 25), "2019-10-25"),
        (datetime.date, datetime.date(2019, 10, 25), "2019-10-25"),
        (DateTime, datetime.datetime(2019, 10, 25, 13, 37), "2019-10-25T13:37:00"),
        (datetime.datetime, datetime.datetime(2019, 10, 25, 13, 37), "2019-10-25T13:37:00"),
        (Time, datetime.time(13, 37), "13:37:00"),
        (datetime.time, datetime.time(13, 37), "13:37:00"),
    ],
)
def test_serialization(typing, instance, serialized):
    @strawberry.type
    class Query:
        @strawberry.field
        def serialize(self, info) -> typing:
            return instance

    schema = strawberry.Schema(Query)

    result = graphql_sync(schema, "{ serialize }")

    assert not result.errors
    assert result.data["serialize"] == serialized


@pytest.mark.parametrize(
    "typing,name,instance,serialized",
    [
        (Date, "Date", datetime.date(2019, 10, 25), "2019-10-25"),
        (datetime.date, "Date", datetime.date(2019, 10, 25), "2019-10-25"),
        (
            DateTime,
            "DateTime",
            datetime.datetime(2019, 10, 25, 13, 37),
            "2019-10-25T13:37:00",
        ),
        (
            datetime.datetime,
            "DateTime",
            datetime.datetime(2019, 10, 25, 13, 37),
            "2019-10-25T13:37:00",
        ),
        (Time, "Time", datetime.time(13, 37), "13:37:00"),
        (datetime.time, "Time", datetime.time(13, 37), "13:37:00"),
    ],
)
def test_deserialization(typing, name, instance, serialized):
    @strawberry.type
    class Query:
        deserialized = None

        @strawberry.field
        def deserialize(self, info, arg: typing) -> bool:
            Query.deserialized = arg
            return True

    schema = strawberry.Schema(Query)

    query = f"""query Deserialize($value: {name}!) {{
        deserialize(arg: $value)
    }}"""
    result = graphql_sync(schema, query, variable_values={"value": serialized})

    assert not result.errors
    assert Query.deserialized == instance


@pytest.mark.parametrize(
    "typing,instance,serialized",
    [
        (Date, datetime.date(2019, 10, 25), "2019-10-25"),
        (datetime.date, datetime.date(2019, 10, 25), "2019-10-25"),
        (DateTime, datetime.datetime(2019, 10, 25, 13, 37), "2019-10-25T13:37:00"),
        (datetime.datetime, datetime.datetime(2019, 10, 25, 13, 37), "2019-10-25T13:37:00"),
        (Time, datetime.time(13, 37), "13:37:00"),
        (datetime.time, datetime.time(13, 37), "13:37:00"),
    ],
)
def test_deserialization_with_parse_literal(typing, instance, serialized):
    @strawberry.type
    class Query:
        deserialized = None

        @strawberry.field
        def deserialize(self, info, arg: typing) -> bool:
            Query.deserialized = arg
            return True

    schema = strawberry.Schema(Query)

    query = f"""query Deserialize {{
        deserialize(arg: "{serialized}")
    }}"""
    result = graphql_sync(schema, query)

    assert not result.errors
    assert Query.deserialized == instance
