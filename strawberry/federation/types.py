from enum import Enum

from strawberry.types.enum import enum
from strawberry.types.scalar import scalar

FieldSet = scalar(str, name="_FieldSet")

LinkImport = scalar(object, name="link__Import")


@enum(name="link__Purpose")
class LinkPurpose(Enum):
    SECURITY = "SECURITY"
    EXECUTION = "EXECUTION"


__all__ = ["FieldSet", "LinkImport", "LinkPurpose"]
