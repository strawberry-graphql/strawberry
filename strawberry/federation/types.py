from enum import Enum

from strawberry.custom_scalar import scalar
from strawberry.enum import enum

Federation__Policy = scalar(str, name="federation__Policy")

Federation__Scope = scalar(str, name="federation__Scope")

FieldSet = scalar(str, name="_FieldSet")

LinkImport = scalar(object, name="link__Import")


@enum(name="link__Purpose")
class LinkPurpose(Enum):
    SECURITY = "SECURITY"
    EXECUTION = "EXECUTION"
