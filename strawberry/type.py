from __future__ import annotations

from typing import Union


StrawberryType = Union[
    "StrawberryEnum",
    "StrawberryInput",
    "StrawberryInterface",
    "StrawberryList",
    "StrawberryObjectType",
    "StrawberryOptional",
    "StrawberryScalar",
    "StrawberryUnion",
]


class StrawberryList:
    def __init__(self, of_type: StrawberryType):
        self.of_type = of_type


class StrawberryOptional:
    def __init__(self, of_type: StrawberryType):
        self.of_type = of_type


# @property
# def type_params(self) -> Optional[List[Type]]:
#     if isinstance(self.type, StrawberryList):
#         assert self.child is not None
#         return self.child.type_params
#
#     if isinstance(self.type, StrawberryUnion):
#         types = self.type.types
#         type_vars = [t for t in types if is_type_var(t)]
#
#         if type_vars:
#             return type_vars
#
#     if is_type_var(self.type):
#         return [self.type]
#
#     if has_type_var(self.type):
#         return get_parameters(self.type)
#
#     return None
