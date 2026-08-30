from enum import Enum
from typing import NewType

from strawberry.types.enum import enum
from strawberry.types.scalar import scalar

FieldSet = NewType("FieldSet", str)
"""Represents a selection set for federation @requires, @provides, @key directives."""
FieldSet._scalar_definition = scalar(  # type: ignore[attr-defined]
    name="_FieldSet",
    serialize=lambda value: value,
    parse_value=str,
    print_definition=False,
)

LinkImport = NewType("LinkImport", object)
"""Represents an import for the @link directive."""
LinkImport._scalar_definition = scalar(  # type: ignore[attr-defined]
    name="link__Import",
    serialize=lambda value: value,
    parse_value=lambda value: value,
    print_definition=False,
)


@enum(name="link__Purpose", print_definition=False)
class LinkPurpose(Enum):
    SECURITY = "SECURITY"
    EXECUTION = "EXECUTION"


__all__ = ["FieldSet", "LinkImport", "LinkPurpose"]
