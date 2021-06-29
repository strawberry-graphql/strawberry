import datetime
import decimal
import uuid
from operator import methodcaller
from typing import Callable
import dateutil.parser
from graphql import GraphQLError

from strawberry.custom_scalar import scalar


def wrap_iso_parser(parser: Callable, _type) -> Callable:
    def inner(value: str):
        try:
            return parser(value)
        except ValueError as e:
            raise GraphQLError(f'Value cannot represent a {_type}: "{value}". {e}')

    return inner


isoformat = methodcaller("isoformat")


Date = scalar(
    datetime.date,
    name="Date",
    description="Date (isoformat)",
    serialize=isoformat,
    parse_value=datetime.date.fromisoformat,
)
DateTime = scalar(
    datetime.datetime,
    name="DateTime",
    description="Date with time (isoformat)",
    serialize=isoformat,
    parse_value=wrap_iso_parser(dateutil.parser.isoparse, "DateTime"),
)
Time = scalar(
    datetime.time,
    name="Time",
    description="Time (isoformat)",
    serialize=isoformat,
    parse_value=datetime.time.fromisoformat,
)

Decimal = scalar(
    decimal.Decimal,
    name="Decimal",
    description="Decimal (fixed-point)",
    serialize=str,
    parse_value=decimal.Decimal,
)

UUID = scalar(
    uuid.UUID,
    name="UUID",
    serialize=str,
    parse_value=uuid.UUID,
)
