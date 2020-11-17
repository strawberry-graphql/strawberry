from typing import Any, Callable, Optional

from mypy.nodes import (
    GDEF,
    Expression,
    IndexExpr,
    MemberExpr,
    NameExpr,
    SymbolTableNode,
    TupleExpr,
    TypeAlias,
    Var,
)
from mypy.plugin import (
    AnalyzeTypeContext,
    ClassDefContext,
    DynamicClassDefContext,
    FunctionContext,
    Plugin,
    SemanticAnalyzerPluginInterface,
)
from mypy.plugins import dataclasses
from mypy.types import AnyType, Type, TypeOfAny, UnionType


class InvalidNodeTypeException(Exception):
    def __init__(self, node: Any) -> None:
        self.message = f"Invalid node type: {str(node)}"

        super().__init__()

    def __str__(self) -> str:
        return self.message


def lazy_type_analyze_callback(ctx: AnalyzeTypeContext) -> Type:
    type_name = ctx.type.args[0]
    type_ = ctx.api.analyze_type(type_name)

    return type_


def strawberry_field_hook(ctx: FunctionContext) -> Type:
    # TODO: check when used as decorator, check type of the caller
    # TODO: check type of resolver if any

    return AnyType(TypeOfAny.special_form)


def private_type_analyze_callback(ctx: AnalyzeTypeContext) -> Type:
    type_name = ctx.type.args[0]
    type_ = ctx.api.analyze_type(type_name)

    return type_


def _get_type_for_expr(expr: Expression, api: SemanticAnalyzerPluginInterface):
    if isinstance(expr, NameExpr):
        # guarding agains invalid nodes, still have to figure out why this happens
        # but sometimes mypy crashes because the internal node of the named type
        # is actually a Var node, which is unexpected, so we do a naive guard here
        # and raise an exception for it.

        if expr.fullname:
            sym = api.lookup_fully_qualified_or_none(expr.fullname)

            if sym and isinstance(sym.node, Var):
                raise InvalidNodeTypeException(sym.node)

        return api.named_type(expr.name)

    if isinstance(expr, IndexExpr):
        type_ = _get_type_for_expr(expr.base, api)
        type_.args = (_get_type_for_expr(expr.index, api),)

        return type_

    if isinstance(expr, MemberExpr):
        if expr.fullname:
            return api.named_type(expr.fullname)
        else:
            raise InvalidNodeTypeException(expr)

    raise ValueError(f"Unsupported expression {type(expr)}")


def union_hook(ctx: DynamicClassDefContext) -> None:
    try:
        # Check if types is passed as a keyword argument
        types = ctx.call.args[ctx.call.arg_names.index("types")]
    except ValueError:
        # Fall back to assuming position arguments
        types = ctx.call.args[1]

    if isinstance(types, TupleExpr):
        try:
            type_ = UnionType(
                tuple(_get_type_for_expr(x, ctx.api) for x in types.items)
            )
        except InvalidNodeTypeException:
            type_alias = TypeAlias(
                AnyType(TypeOfAny.from_error),
                fullname=ctx.api.qualified_name(ctx.name),
                line=ctx.call.line,
                column=ctx.call.column,
            )

            ctx.api.add_symbol_table_node(
                ctx.name,
                SymbolTableNode(GDEF, type_alias, plugin_generated=False),
            )

            return

        type_alias = TypeAlias(
            type_,
            fullname=ctx.api.qualified_name(ctx.name),
            line=ctx.call.line,
            column=ctx.call.column,
        )

        ctx.api.add_symbol_table_node(
            ctx.name, SymbolTableNode(GDEF, type_alias, plugin_generated=False)
        )


def enum_hook(ctx: DynamicClassDefContext) -> None:
    first_argument = ctx.call.args[0]

    if isinstance(first_argument, NameExpr):
        if not first_argument.node:
            ctx.api.defer()

            return

        if isinstance(first_argument.node, Var):
            var_type = first_argument.node.type or AnyType(
                TypeOfAny.implementation_artifact
            )

            type_alias = TypeAlias(
                var_type,
                fullname=ctx.api.qualified_name(ctx.name),
                line=ctx.call.line,
                column=ctx.call.column,
            )

            ctx.api.add_symbol_table_node(
                ctx.name, SymbolTableNode(GDEF, type_alias, plugin_generated=False)
            )
            return

    try:
        enum_type = _get_type_for_expr(first_argument, ctx.api)

        type_alias = TypeAlias(
            enum_type,
            fullname=ctx.api.qualified_name(ctx.name),
            line=ctx.call.line,
            column=ctx.call.column,
        )
    except InvalidNodeTypeException:
        type_alias = TypeAlias(
            AnyType(TypeOfAny.from_error),
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

        if "strawberry.enum" in fullname:
            return enum_hook

        return None

    def get_function_hook(
        self, fullname: str
    ) -> Optional[Callable[[FunctionContext], Type]]:
        if fullname == "strawberry.field.field":
            return strawberry_field_hook

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
