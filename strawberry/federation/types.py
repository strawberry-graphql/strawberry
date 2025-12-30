from enum import Enum
from typing import NewType

from strawberry.types.enum import enum

FieldSet = NewType("FieldSet", str)
"""Represents a selection set for federation @requires, @provides, @key directives."""

LinkImport = NewType("LinkImport", object)
"""Represents an import for the @link directive."""


@enum(name="link__Purpose")
class LinkPurpose(Enum):
    SECURITY = "SECURITY"
    EXECUTION = "EXECUTION"


__all__ = ["FieldSet", "LinkImport", "LinkPurpose"]
