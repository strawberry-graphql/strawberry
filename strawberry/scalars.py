from __future__ import annotations

from typing import TYPE_CHECKING, Any, NewType

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


def is_scalar(
    annotation: Any,
    scalar_registry: Mapping[object, ScalarWrapper | ScalarDefinition],
) -> bool:
    if annotation in scalar_registry:
        return True

    return hasattr(annotation, "_scalar_definition")


__all__ = [
    "ID",
    "JSON",
    "Base16",
    "Base32",
    "Base64",
    "is_scalar",
]
