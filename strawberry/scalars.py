from datetime import date, datetime, time
from decimal import Decimal
from typing import NewType, Type

from .custom_scalar import SCALAR_REGISTRY


ID = NewType("ID", str)
SCALAR_TYPES = [int, str, float, bytes, bool, datetime, date, time, Decimal]


def is_scalar(annotation: Type) -> bool:
    type = getattr(annotation, "__supertype__", annotation)

    if type in SCALAR_REGISTRY:
        return True

    if type in SCALAR_TYPES:
        return True

    return hasattr(annotation, "_scalar_definition")
