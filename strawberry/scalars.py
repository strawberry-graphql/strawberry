from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, NewType
from uuid import UUID


ID = NewType("ID", str)
SCALAR_TYPES = [int, str, float, bytes, bool, ID, UUID, datetime, date, time, Decimal]


def is_scalar(annotation: Any) -> bool:
    type_ = getattr(annotation, "__supertype__", annotation)

    if type_ in SCALAR_TYPES:
        return True

    return hasattr(annotation, "_scalar_definition")
