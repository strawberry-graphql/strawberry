import datetime

import pytest

import dateutil.tz

import strawberry


@pytest.mark.parametrize(
    "typing,instance,serialized",
    [
        (datetime.date, datetime.date(2019, 10, 25), "2019-10-25"),
        (
            datetime.datetime,
            datetime.datetime(2019, 10, 25, 13, 37),
            "2019-10-25T13:37:00",
        ),
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

    result = schema.execute_sync("{ serialize }")

    assert not result.errors
    assert result.data["serialize"] == serialized


@pytest.mark.parametrize(
    "typing,name,instance,serialized",
    [
        (datetime.date, "Date", datetime.date(2019, 10, 25), "2019-10-25"),
        (
            datetime.datetime,
            "DateTime",
            datetime.datetime(2019, 10, 25, 13, 37),
            "2019-10-25T13:37:00",
        ),
        (
            datetime.datetime,
            "DateTime",
            datetime.datetime(2019, 10, 25, 13, 37, tzinfo=dateutil.tz.tzutc()),
            "2019-10-25T13:37:00Z",
        ),
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
    result = schema.execute_sync(query, variable_values={"value": serialized})

    assert not result.errors
    assert Query.deserialized == instance


@pytest.mark.parametrize(
    "typing,instance,serialized",
    [
        (datetime.date, datetime.date(2019, 10, 25), "2019-10-25"),
        (
            datetime.datetime,
            datetime.datetime(2019, 10, 25, 13, 37),
            "2019-10-25T13:37:00",
        ),
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
    result = schema.execute_sync(query)

    assert not result.errors
    assert Query.deserialized == instance
