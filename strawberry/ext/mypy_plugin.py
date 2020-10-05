from typing import Callable, Optional

from mypy.nodes import GDEF, Block, ClassDef, SymbolTableNode
from mypy.plugin import (
    AnalyzeTypeContext,
    ClassDefContext,
    DynamicClassDefContext,
    Plugin,
)
from mypy.plugins import dataclasses
from mypy.types import Type


def lazy_type_analyze_callback(ctx: AnalyzeTypeContext) -> Type:
    type_name = ctx.type.args[0]
    type_ = ctx.api.analyze_type(type_name)

    return type_


def private_type_analyze_callback(ctx: AnalyzeTypeContext) -> Type:
    type_name = ctx.type.args[0]
    type_ = ctx.api.analyze_type(type_name)

    return type_


def union_hook(ctx: DynamicClassDefContext) -> None:
    # TODO: use these types to construct a propert return type (now it is Any)
    # >>> types = ctx.call.args[1]
    # >>> type_ = UnionType(tuple(ctx.api.named_type(x.name) for x in types.items))

    class_def = ClassDef(ctx.name, Block([]))
    class_def.fullname = ctx.api.qualified_name(ctx.name)
    info = ctx.api.make_empty_type_info(class_def)  # type: ignore

    ctx.api.add_symbol_table_node(ctx.name, SymbolTableNode(GDEF, info))


class StrawberryPlugin(Plugin):
    def get_dynamic_class_hook(
        self, fullname: str
    ) -> Optional[Callable[[DynamicClassDefContext], None]]:
        if "strawberry.union.union" in fullname:
            return union_hook

        return None

    def get_type_analyze_hook(self, fullname: str):
        if fullname == "strawberry.lazy_type.LazyType":
            return lazy_type_analyze_callback

        if any(
            name in fullname
            for name in {"strawberry.private.Private", "strawberry.Private"}
        ):
            return private_type_analyze_callback

        return None

    def get_class_decorator_hook(
        self, fullname: str
    ) -> Optional[Callable[[ClassDefContext], None]]:
        if any(
            strawberry_decorator in fullname
            for strawberry_decorator in {
                "strawberry.type",
                "strawberry.federation.type",
                "strawberry.input",
                "strawberry.interface",
            }
        ):
            return dataclasses.dataclass_class_maker_callback
        return None


def plugin(version: str):
    return StrawberryPlugin
