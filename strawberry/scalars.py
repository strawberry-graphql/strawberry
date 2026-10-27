from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, NewType, get_args, get_origin

from strawberry.types.scalar import ScalarDefinition

if TYPE_CHECKING:
    from collections.abc import Mapping


ID = NewType("ID", str)
"""Represent the GraphQL `ID` scalar type."""

JSON = NewType("JSON", object)
"""Represent the GraphQL `JSON` scalar type for arbitrary JSON values."""

Base16 = NewType("Base16", bytes)
"""Represent binary data as Base16-encoded (hexadecimal) strings."""

Base32 = NewType("Base32", bytes)
"""Represent binary data as Base32-encoded strings."""

Base64 = NewType("Base64", bytes)
"""Represent binary data as Base64-encoded strings."""


def get_scalar_definition(
    annotation: Any,
    scalar_registry: Mapping[object, ScalarDefinition],
    *,
    scalar_overrides: Mapping[object, ScalarDefinition] | None = None,
) -> ScalarDefinition | None:
    if annotation in scalar_registry:
        return scalar_registry[annotation]

    if get_origin(annotation) is Annotated:
        underlying, *metadata = get_args(annotation)
        if scalar_overrides and underlying in scalar_overrides:
            return scalar_overrides[underlying]
        for item in metadata:
            if isinstance(item, ScalarDefinition):
                return item
        return get_scalar_definition(
            underlying, scalar_registry, scalar_overrides=scalar_overrides
        )

    # Keep scalar checks consistent for schema generation and argument conversion.
    origin = get_origin(annotation)
    if origin is not None and origin in scalar_registry:
        return scalar_registry[origin]

    return getattr(annotation, "_scalar_definition", None)


def is_scalar(
    annotation: Any,
    scalar_registry: Mapping[object, ScalarDefinition],
) -> bool:
    return get_scalar_definition(annotation, scalar_registry) is not None


__all__ = [
    "ID",
    "JSON",
    "Base16",
    "Base32",
    "Base64",
    "is_scalar",
]
