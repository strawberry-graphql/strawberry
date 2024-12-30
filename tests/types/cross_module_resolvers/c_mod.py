import strawberry

from . import a_mod, b_mod, x_mod
from .a_mod import AObject as C_AObject
from .b_mod import BObject as C_BObject


def c_inheritance_resolver() -> list["CInheritance"]:
    pass


def c_composition_resolver() -> list["CComposition"]:
    pass


def c_composition_by_name_resolver() -> list["CCompositionByName"]:
    pass


@strawberry.type
class CInheritance(a_mod.AObject, b_mod.BObject):
    pass


@strawberry.type
class CComposition:
    a_list: list[a_mod.AObject]
    b_list: list[b_mod.BObject]


@strawberry.type
class CCompositionByName:
    a_list: list["C_AObject"]
    b_list: list["C_BObject"]

    @strawberry.field
    def a_method(self) -> list["C_AObject"]:
        return self.a_list

    @strawberry.field
    def b_method(self) -> list["C_BObject"]:
        return self.b_list


@strawberry.type
class CCompositionByNameWithResolvers:
    a_list: list["C_AObject"] = strawberry.field(resolver=a_mod.a_resolver)
    b_list: list["C_BObject"] = strawberry.field(resolver=b_mod.b_resolver)


@strawberry.type
class CCompositionByNameWithTypelessResolvers:
    a_list: list["C_AObject"] = strawberry.field(resolver=x_mod.typeless_resolver)
    b_list: list["C_BObject"] = strawberry.field(resolver=x_mod.typeless_resolver)


@strawberry.type
class CCompositionOnlyResolvers:
    a_list = strawberry.field(resolver=a_mod.a_resolver)
    b_list = strawberry.field(resolver=b_mod.b_resolver)
