"""Shared behaviour of the scalars built on ``wrap_parser``."""

import datetime
import uuid

import pytest
from graphql import GraphQLError

import strawberry


@strawberry.type
class Query:
    @strawberry.field
    def uuid_field(self, value: uuid.UUID) -> str:
        return str(value)

    @strawberry.field
    def date_field(self, value: datetime.date) -> str:
        return str(value)

    @strawberry.field
    def time_field(self, value: datetime.time) -> str:
        return str(value)

    @strawberry.field
    def datetime_field(self, value: datetime.datetime) -> str:
        return str(value)


schema = strawberry.Schema(query=Query)


@pytest.mark.parametrize(
    ("field", "type_name"),
    [
        ("uuidField", "UUID"),
        ("dateField", "Date"),
        ("timeField", "Time"),
        ("datetimeField", "DateTime"),
    ],
)
@pytest.mark.parametrize("value", [469610.0, 123, True, ["a"], {"a": 1}])
def test_non_string_variable_is_reported_as_invalid_input(field, type_name, value):
    """A non-string variable is invalid input, not a server error.

    These parsers accept only strings and raise ``AttributeError`` or
    ``TypeError`` on anything else. That used to escape ``wrap_parser`` and
    reach the client as the stdlib's own complaint, e.g. "'float' object has no
    attribute 'replace'", fingerprinted on frames like ``uuid.py __init__``.
    """
    result = schema.execute_sync(
        f"query ($value: {type_name}!) {{ {field}(value: $value) }}",
        variable_values={"value": value},
    )

    assert result.errors
    error = result.errors[0]
    assert isinstance(error, GraphQLError)
    assert f'Value cannot represent a {type_name}: "{value}".' in error.message
    # The parser's internals must not leak into a client-facing message.
    assert "has no attribute" not in error.message
    assert not isinstance(error.original_error, (AttributeError, TypeError))


@pytest.mark.parametrize(
    ("field", "type_name", "value", "expected"),
    [
        (
            "uuidField",
            "UUID",
            "12345678-1234-5678-1234-567812345678",
            "12345678-1234-5678-1234-567812345678",
        ),
        ("dateField", "Date", "2023-05-17", "2023-05-17"),
        ("timeField", "Time", "12:34:56", "12:34:56"),
        (
            "datetimeField",
            "DateTime",
            "2023-05-17T12:34:56",
            "2023-05-17 12:34:56",
        ),
    ],
)
def test_valid_strings_still_parse(field, type_name, value, expected):
    result = schema.execute_sync(
        f"query ($value: {type_name}!) {{ {field}(value: $value) }}",
        variable_values={"value": value},
    )

    assert not result.errors
    assert result.data[field] == expected
