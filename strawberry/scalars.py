from datetime import date, datetime, time
from decimal import Decimal
from typing import NewType, Type


ID = NewType("ID", str)


# TODO: these need to be update when defining a custom scalar
SCALAR_TYPES = [int, str, float, bytes, bool, datetime, date, time, Decimal]


def is_scalar(annotation: Type) -> bool:
    return getattr(annotation, "__supertype__", annotation) in SCALAR_TYPES or hasattr(
        annotation, "_scalar_definition"
    )
