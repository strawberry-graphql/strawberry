import datetime
import decimal
import uuid
from collections.abc import Callable
from operator import methodcaller

import dateutil.parser
from graphql import GraphQLError

from strawberry.types.scalar import ScalarDefinition


def wrap_parser(parser: Callable, type_: str) -> Callable:
    def inner(value: str) -> object:
        try:
            return parser(value)
        except ValueError as e:
            raise GraphQLError(  # noqa: B904
                f'Value cannot represent a {type_}: "{value}". {e}'
            )

    return inner


def parse_decimal(value: object) -> decimal.Decimal:
    try:
        return decimal.Decimal(str(value))
    except decimal.DecimalException:
        raise GraphQLError(f'Value cannot represent a Decimal: "{value}".')  # noqa: B904


isoformat = methodcaller("isoformat")


DateDefinition: ScalarDefinition = ScalarDefinition(
    name="Date",
    description="Date (isoformat)",
    specified_by_url=None,
    serialize=isoformat,
    parse_value=wrap_parser(datetime.date.fromisoformat, "Date"),
    parse_literal=None,
    origin=datetime.date,
)

DateTimeDefinition: ScalarDefinition = ScalarDefinition(
    name="DateTime",
    description="Date with time (isoformat)",
    specified_by_url=None,
    serialize=isoformat,
    parse_value=wrap_parser(dateutil.parser.isoparse, "DateTime"),
    parse_literal=None,
    origin=datetime.datetime,
)

TimeDefinition: ScalarDefinition = ScalarDefinition(
    name="Time",
    description="Time (isoformat)",
    specified_by_url=None,
    serialize=isoformat,
    parse_value=wrap_parser(datetime.time.fromisoformat, "Time"),
    parse_literal=None,
    origin=datetime.time,
)

DecimalDefinition: ScalarDefinition = ScalarDefinition(
    name="Decimal",
    description="Decimal (fixed-point)",
    specified_by_url=None,
    serialize=str,
    parse_value=parse_decimal,
    parse_literal=None,
    origin=decimal.Decimal,
)

UUIDDefinition: ScalarDefinition = ScalarDefinition(
    name="UUID",
    description=None,
    specified_by_url=None,
    serialize=str,
    parse_value=wrap_parser(uuid.UUID, "UUID"),
    parse_literal=None,
    origin=uuid.UUID,
)


def _verify_void(x: None) -> None:
    if x is not None:
        raise ValueError(f"Expected 'None', got '{x}'")


VoidDefinition: ScalarDefinition = ScalarDefinition(
    name="Void",
    description="Represents NULL values",
    specified_by_url=None,
    serialize=_verify_void,
    parse_value=_verify_void,
    parse_literal=None,
    origin=type(None),
)


__all__ = [
    "DateDefinition",
    "DateTimeDefinition",
    "DecimalDefinition",
    "TimeDefinition",
    "UUIDDefinition",
    "VoidDefinition",
]
