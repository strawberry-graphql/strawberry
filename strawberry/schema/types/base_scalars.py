import datetime
import decimal
import uuid
from collections.abc import Callable
from operator import methodcaller

import dateutil.parser
from graphql import GraphQLError

from strawberry.types.scalar import ScalarDefinition


def wrap_parser(
    parser: Callable[[str], object],
    type_: str,
    exceptions: tuple[type[Exception], ...] = (ValueError,),
    include_error: bool = True,
    accept_non_string: bool = False,
) -> Callable[[object], object]:
    """Wrap a string parser so any invalid input becomes a clean coercion error.

    Non-string input is rejected up front so the parser can never crash with
    ``AttributeError``/``TypeError`` on unexpected value types and surface as
    a server-side error. ``accept_non_string`` stringifies non-string input
    instead of rejecting it, for scalars that accept it by design (``Decimal``
    accepts numeric input this way).
    """

    def inner(value: object) -> object:
        if not isinstance(value, str):
            if not accept_non_string:
                raise GraphQLError(
                    f'Value cannot represent a {type_}: "{value}". Expected a string.'
                )
            value = str(value)
        try:
            return parser(value)
        except exceptions as e:
            detail = f" {e}" if include_error else ""
            raise GraphQLError(
                f'Value cannot represent a {type_}: "{value}".{detail}'
            ) from None

    return inner


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
    parse_value=wrap_parser(
        decimal.Decimal,
        "Decimal",
        exceptions=(decimal.DecimalException,),
        include_error=False,
        accept_non_string=True,
    ),
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
