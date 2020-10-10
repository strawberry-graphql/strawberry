from typing import Callable, Optional

from mypy.nodes import (
    GDEF,
    Expression,
    IndexExpr,
    NameExpr,
    SymbolTableNode,
    TupleExpr,
    TypeAlias,
)
from mypy.plugin import (
    AnalyzeTypeContext,
    ClassDefContext,
    DynamicClassDefContext,
    Plugin,
    SemanticAnalyzerPluginInterface,
)
from mypy.plugins import dataclasses
from mypy.types import Type, UnionType


def lazy_type_analyze_callback(ctx: AnalyzeTypeContext) -> Type:
    type_name = ctx.type.args[0]
    type_ = ctx.api.analyze_type(type_name)

    return type_


def private_type_analyze_callback(ctx: AnalyzeTypeContext) -> Type:
    type_name = ctx.type.args[0]
    type_ = ctx.api.analyze_type(type_name)

    return type_


def _get_type_for_expr(expr: Expression, api: SemanticAnalyzerPluginInterface):
    if isinstance(expr, NameExpr):
        return api.named_type(expr.name)

    if isinstance(expr, IndexExpr):
        type_ = _get_type_for_expr(expr.base, api)
        type_.args = (_get_type_for_expr(expr.index, api),)

        return type_

    raise ValueError(f"Unsupported expression f{type(expr)}")


def union_hook(ctx: DynamicClassDefContext) -> None:
    types = ctx.call.args[1]

    if isinstance(types, TupleExpr):
        type_ = UnionType(tuple(_get_type_for_expr(x, ctx.api) for x in types.items))

        type_alias = TypeAlias(
            type_,
            fullname=ctx.api.qualified_name(ctx.name),
            line=ctx.call.line,
            column=ctx.call.column,
        )

        ctx.api.add_symbol_table_node(
            ctx.name, SymbolTableNode(GDEF, type_alias, plugin_generated=False)
        )


class StrawberryPlugin(Plugin):
    def get_dynamic_class_hook(
        self, fullname: str
    ) -> Optional[Callable[[DynamicClassDefContext], None]]:
        # TODO: investigate why we need this instead of `strawberry.union.union` on CI
        # we have the same issue in the other hooks
        if "strawberry.union" in fullname:
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
