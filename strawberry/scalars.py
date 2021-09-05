from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Dict, NewType, Union
from uuid import UUID

from .custom_scalar import ScalarDefinition, ScalarWrapper


ID = NewType("ID", str)
SCALAR_TYPES = [int, str, float, bool, ID, UUID, datetime, date, time, Decimal]


def is_scalar(
    annotation: Any,
    scalar_registry: Dict[object, Union[ScalarWrapper, ScalarDefinition]],
) -> bool:
    if annotation in scalar_registry:
        return True

    type_ = getattr(annotation, "__supertype__", annotation)

    if type_ in SCALAR_TYPES:
        return True

    return hasattr(annotation, "_scalar_definition")
