from __future__ import annotations

import typing
from typing import get_args, get_origin

LiteralPythonType = type[str] | type[int] | type[bool]

_SUPPORTED_LITERAL_TYPES: tuple[LiteralPythonType, ...] = (str, int, bool)


def is_literal(annotation: object) -> bool:
    return annotation is typing.Literal or get_origin(annotation) is typing.Literal


def get_literal_python_type(annotation: object) -> LiteralPythonType:
    values = get_args(annotation)

    if not values:
        raise TypeError("Literal must contain at least one value")

    value_types = {type(value) for value in values}

    if len(value_types) != 1:
        raise TypeError(f"Literal values must all have the same type; got {values!r}")

    value_type = value_types.pop()

    if value_type not in _SUPPORTED_LITERAL_TYPES:
        raise TypeError(
            f"Unsupported Literal values {values!r}; "
            "only str, int, and bool values are supported"
        )

    return value_type


def is_valid_literal_value(annotation: object, value: object) -> bool:
    get_literal_python_type(annotation)

    return any(
        type(value) is type(expected) and value == expected
        for expected in get_args(annotation)
    )


__all__ = ["get_literal_python_type", "is_literal", "is_valid_literal_value"]
