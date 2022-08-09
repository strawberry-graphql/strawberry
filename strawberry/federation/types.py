from enum import Enum

from strawberry.custom_scalar import scalar
from strawberry.enum import enum


def serialize_field_set(value: str) -> str:
    # breakpoint()
    return value


FieldSet = scalar(str, name="_FieldSet", serialize=serialize_field_set)

LinkImport = scalar(object, name="link__Import")


@enum(name="link__Purpose")
class LinkPurpose(Enum):
    SECURITY = "SECURITY"
    EXECUTION = "EXECUTION"
