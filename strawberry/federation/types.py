from enum import Enum

from strawberry.custom_scalar import scalar
from strawberry.enum import enum

FieldSet = scalar(str, name="_FieldSet")

LinkImport = scalar(object, name="link__Import")


@enum(name="link__Purpose")
class LinkPurpose(Enum):
    SECURITY = "SECURITY"
    EXECUTION = "EXECUTION"
