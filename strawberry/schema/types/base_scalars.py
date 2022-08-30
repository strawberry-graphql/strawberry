import datetime
import decimal
import uuid
from operator import methodcaller
from typing import Callable

import dateutil.parser

from graphql import GraphQLError
from graphql.type.scalars import GraphQLID

from strawberry.custom_scalar import scalar


def wrap_parser(parser: Callable, type_: str) -> Callable:
    def inner(value: str):
        try:
            return parser(value)
        except ValueError as e:
            raise GraphQLError(f'Value cannot represent a {type_}: "{value}". {e}')

    return inner


def parse_decimal(value: object) -> decimal.Decimal:
    try:
        return decimal.Decimal(str(value))
    except decimal.DecimalException:
        raise GraphQLError(f'Value cannot represent a Decimal: "{value}".')


isoformat = methodcaller("isoformat")


Date = scalar(
    datetime.date,
    name="Date",
    description="Date (isoformat)",
    serialize=isoformat,
    parse_value=wrap_parser(datetime.date.fromisoformat, "Date"),
)
DateTime = scalar(
    datetime.datetime,
    name="DateTime",
    description="Date with time (isoformat)",
    serialize=isoformat,
    parse_value=wrap_parser(dateutil.parser.isoparse, "DateTime"),
)
Time = scalar(
    datetime.time,
    name="Time",
    description="Time (isoformat)",
    serialize=isoformat,
    parse_value=wrap_parser(datetime.time.fromisoformat, "Time"),
)

Decimal = scalar(
    decimal.Decimal,
    name="Decimal",
    description="Decimal (fixed-point)",
    serialize=str,
    parse_value=parse_decimal,
)

UUID = scalar(
    uuid.UUID,
    name="UUID",
    serialize=str,
    parse_value=wrap_parser(uuid.UUID, "UUID"),
)


def _verify_void(x) -> None:
    if x is not None:
        raise ValueError(f"Expected 'None', got '{x}'")


Void = scalar(
    type(None),
    name="Void",
    serialize=_verify_void,
    parse_value=_verify_void,
    description="Represents NULL values",
)

ID = scalar(
    name="ID",
    description="The `ID` scalar type represents a unique identifier,"
    " often used to refetch an object or as key for a cache."
    " The ID type appears in a JSON response as a String; however,"
    " it is not intended to be human-readable. When expected as an"
    ' input type, any string (such as `"4"`) or integer (such as'
    " `4`) input value will be accepted as an ID.",
    serialize=GraphQLID.serialize,
    parse_value=GraphQLID.parse_value,
    parse_literal=GraphQLID.parse_literal,
    specified_by_url="https://spec.graphql.org/June2018/#sec-ID",
)
