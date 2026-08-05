from __future__ import annotations

from typing import TYPE_CHECKING, Any, NewType, cast, get_origin

if TYPE_CHECKING:
    from collections.abc import Mapping

    from strawberry.types.scalar import ScalarDefinition, ScalarWrapper


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


def _get_scalar_definition(
    annotation: Any,
    scalar_registry: Mapping[object, ScalarWrapper | ScalarDefinition],
) -> ScalarDefinition | None:
    while True:
        if annotation in scalar_registry:
            scalar_definition = scalar_registry[annotation]
            return cast(
                "ScalarDefinition",
                getattr(
                    scalar_definition,
                    "_scalar_definition",
                    scalar_definition,
                ),
            )

        origin = get_origin(annotation)
        if origin is not None and origin in scalar_registry:
            scalar_definition = scalar_registry[origin]
            return cast(
                "ScalarDefinition",
                getattr(
                    scalar_definition,
                    "_scalar_definition",
                    scalar_definition,
                ),
            )

        if hasattr(annotation, "_scalar_definition"):
            return cast("ScalarDefinition", annotation._scalar_definition)

        if not isinstance(annotation, NewType):
            return None

        annotation = annotation.__supertype__


def is_scalar(
    annotation: Any,
    scalar_registry: Mapping[object, ScalarWrapper | ScalarDefinition],
) -> bool:
    return _get_scalar_definition(annotation, scalar_registry) is not None


__all__ = [
    "ID",
    "JSON",
    "Base16",
    "Base32",
    "Base64",
    "is_scalar",
]
