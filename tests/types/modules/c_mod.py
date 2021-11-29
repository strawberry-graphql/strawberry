from typing import List

import strawberry

from . import a_mod, b_mod, x_mod


def c_inheritance_resolver() -> List["CInheritance"]:
    pass


def c_composition_resolver() -> List["CComposition"]:
    pass


def c_composition_by_name_resolver() -> List["CCompositionByName"]:
    pass


@strawberry.type
class CInheritance(a_mod.AObject, b_mod.BObject):
    pass


@strawberry.type
class CComposition:
    a_list: List[a_mod.AObject]
    b_list: List[b_mod.BObject]


@strawberry.type
class CCompositionByName:
    a_list: List["C_AObject"]
    b_list: List["C_BObject"]


@strawberry.type
class CCompositionByNameWithResolvers:
    a_list: List["C_AObject"] = strawberry.field(resolver=a_mod.a_resolver)
    b_list: List["C_BObject"] = strawberry.field(resolver=b_mod.b_resolver)


@strawberry.type
class CCompositionByNameWithTypelessResolvers:
    a_list: List["C_AObject"] = strawberry.field(resolver=x_mod.typeless_resolver)
    b_list: List["C_BObject"] = strawberry.field(resolver=x_mod.typeless_resolver)


@strawberry.type
class CCompositionOnlyResolvers:
    a_list = strawberry.field(resolver=a_mod.a_resolver)
    b_list = strawberry.field(resolver=b_mod.b_resolver)


from .a_mod import AObject as C_AObject
from .b_mod import BObject as C_BObject
