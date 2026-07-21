from __future__ import annotations

import re
import warnings
from decimal import Decimal
from typing import (
    TYPE_CHECKING,
    Any,
    cast,
)

from mypy.nodes import (
    ARG_OPT,
    ARG_POS,
    ARG_STAR2,
    MDEF,
    Argument,
    Block,
    CallExpr,
    CastExpr,
    FuncDef,
    IndexExpr,
    MemberExpr,
    NameExpr,
    PassStmt,
    SymbolTableNode,
    Var,
)
from mypy.plugin import (
    Plugin,
    SemanticAnalyzerPluginInterface,
)
from mypy.plugins.common import _get_argument, add_method
from mypy.semanal_shared import set_callable_name
from mypy.types import (
    AnyType,
    CallableType,
    Instance,
    NoneType,
    Type,
    TypeOfAny,
    TypeVarType,
    UnionType,
)
from mypy.typevars import fill_typevars
from mypy.util import get_unique_redefinition_name

if TYPE_CHECKING:
    from collections.abc import Callable

    from mypy.nodes import ClassDef, Expression
    from mypy.plugin import (
        CheckerPluginInterface,
        ClassDefContext,
    )

VERSION_RE = re.compile(r"(^0|^(?:[1-9][0-9]*))\.(0|(?:[1-9][0-9]*))")
FALLBACK_VERSION = Decimal("0.800")


class MypyVersion:
    VERSION: Decimal = FALLBACK_VERSION


class InvalidNodeTypeException(Exception):
    def __init__(self, node: Any) -> None:
        message = f"Invalid node type: {node!s}"
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        return self.message


def _get_named_type(name: str, api: SemanticAnalyzerPluginInterface) -> Any:
    if "." in name:
        return api.named_type_or_none(name)
    return api.named_type(name)


def _get_type_for_expr(expr: Expression, api: SemanticAnalyzerPluginInterface) -> Type:
    if isinstance(expr, NameExpr):
        if expr.fullname:
            sym = api.lookup_fully_qualified_or_none(expr.fullname)
            if sym and isinstance(sym.node, Var):
                raise InvalidNodeTypeException(sym.node)
        return _get_named_type(expr.fullname or expr.name, api)

    if isinstance(expr, IndexExpr):
        type_ = _get_type_for_expr(expr.base, api)
        type_.args = (_get_type_for_expr(expr.index, api),)  # type: ignore
        return type_

    if isinstance(expr, MemberExpr):
        if expr.fullname:
            return _get_named_type(expr.fullname, api)
        raise InvalidNodeTypeException(expr)

    if isinstance(expr, CallExpr):
        if expr.analyzed:
            return _get_type_for_expr(expr.analyzed, api)
        raise InvalidNodeTypeException(expr)

    if isinstance(expr, CastExpr):
        return expr.type

    raise ValueError(f"Unsupported expression {type(expr)}")


def add_static_method_to_class(
    api: SemanticAnalyzerPluginInterface | CheckerPluginInterface,
    cls: ClassDef,
    name: str,
    args: list[Argument],
    return_type: Type,
    tvar_def: TypeVarType | None = None,
) -> None:
    info = cls.info

    if name in info.names:
        sym = info.names[name]
        if sym.plugin_generated and isinstance(sym.node, FuncDef):
            cls.defs.body.remove(sym.node)

    if Decimal("0.93") > MypyVersion.VERSION:
        function_type = api.named_type("__builtins__.function")  # type: ignore[union-attr]
    elif isinstance(api, SemanticAnalyzerPluginInterface):
        function_type = api.named_type("builtins.function")
    else:
        function_type = api.named_generic_type("builtins.function", [])

    arg_types, arg_names, arg_kinds = [], [], []
    for arg in args:
        assert arg.type_annotation, "All arguments must be fully typed."
        arg_types.append(arg.type_annotation)
        arg_names.append(arg.variable.name)
        arg_kinds.append(arg.kind)

    signature = CallableType(
        arg_types, arg_kinds, arg_names, return_type, function_type
    )
    if tvar_def:
        signature.variables = [tvar_def]  # type: ignore[assignment]

    func = FuncDef(name, args, Block([PassStmt()]))
    func.is_static = True
    func.info = info
    func.type = set_callable_name(signature, func)
    func._fullname = f"{info.fullname}.{name}"
    func.line = info.line

    if name in info.names:
        r_name = get_unique_redefinition_name(name, info.names)
        info.names[r_name] = info.names[name]

    info.names[name] = SymbolTableNode(MDEF, func, plugin_generated=True)
    info.defn.defs.body.append(func)


def strawberry_pydantic_class_callback(ctx: ClassDefContext) -> None:
    model_expression = _get_argument(call=cast("CallExpr", ctx.reason), name="model")
    if model_expression is None:
        ctx.api.fail("model argument in decorator failed to be parsed", ctx.reason)
        return

    # Add __init__ with **kwargs
    init_args = [Argument(Var("kwargs"), AnyType(TypeOfAny.explicit), None, ARG_STAR2)]
    add_method(ctx, "__init__", init_args, NoneType())

    try:
        model_type = cast("Instance", _get_type_for_expr(model_expression, ctx.api))
    except (InvalidNodeTypeException, ValueError):
        model_type = None

    if model_type is not None:
        # Add to_pydantic() -> ModelType
        if "to_pydantic" not in ctx.cls.info.names:
            to_pydantic_args = [
                Argument(Var("kwargs"), AnyType(TypeOfAny.explicit), None, ARG_STAR2)
            ]
            add_method(ctx, "to_pydantic", to_pydantic_args, model_type)

        # Add from_pydantic(instance, extra) as static method
        if "from_pydantic" not in ctx.cls.info.names:
            model_argument = Argument(
                variable=Var(name="instance", type=model_type),
                type_annotation=model_type,
                initializer=None,
                kind=ARG_POS,
            )
            extra_type = ctx.api.named_type(
                "builtins.dict",
                [ctx.api.named_type("builtins.str"), AnyType(TypeOfAny.explicit)],
            )
            extra_argument = Argument(
                variable=Var(name="extra", type=UnionType([NoneType(), extra_type])),
                type_annotation=UnionType([NoneType(), extra_type]),
                initializer=None,
                kind=ARG_OPT,
            )

            add_static_method_to_class(
                ctx.api,
                ctx.cls,
                name="from_pydantic",
                args=[model_argument, extra_argument],
                return_type=fill_typevars(ctx.cls.info),
            )
    # Fallback: add methods with Any types
    else:
        if "to_pydantic" not in ctx.cls.info.names:
            to_pydantic_args = [
                Argument(Var("kwargs"), AnyType(TypeOfAny.explicit), None, ARG_STAR2)
            ]
            add_method(
                ctx, "to_pydantic", to_pydantic_args, AnyType(TypeOfAny.explicit)
            )

        if "from_pydantic" not in ctx.cls.info.names:
            fallback_model_argument = Argument(
                variable=Var(name="instance", type=AnyType(TypeOfAny.explicit)),
                type_annotation=AnyType(TypeOfAny.explicit),
                initializer=None,
                kind=ARG_POS,
            )
            fallback_extra_argument = Argument(
                variable=Var(name="extra", type=AnyType(TypeOfAny.explicit)),
                type_annotation=AnyType(TypeOfAny.explicit),
                initializer=None,
                kind=ARG_OPT,
            )
            add_static_method_to_class(
                ctx.api,
                ctx.cls,
                name="from_pydantic",
                args=[fallback_model_argument, fallback_extra_argument],
                return_type=fill_typevars(ctx.cls.info),
            )


class StrawberryPlugin(Plugin):
    def get_class_decorator_hook(
        self, fullname: str
    ) -> Callable[[ClassDefContext], None] | None:
        if self._is_strawberry_pydantic_decorator(fullname):
            return strawberry_pydantic_class_callback
        return None

    _PYDANTIC_DECORATORS = frozenset(
        {
            "strawberry.experimental.pydantic.object_type.type",
            "strawberry.experimental.pydantic.object_type.input",
            "strawberry.experimental.pydantic.object_type.interface",
            "strawberry.experimental.pydantic.error_type.error_type",
            "strawberry.experimental.pydantic.type",
            "strawberry.experimental.pydantic.input",
            "strawberry.experimental.pydantic.error_type",
        }
    )

    def _is_strawberry_pydantic_decorator(self, fullname: str) -> bool:
        return fullname in self._PYDANTIC_DECORATORS


def plugin(version: str) -> type[StrawberryPlugin]:
    match = VERSION_RE.match(version)
    if match:
        MypyVersion.VERSION = Decimal(".".join(match.groups()))
    else:
        MypyVersion.VERSION = FALLBACK_VERSION
        warnings.warn(
            f"Mypy version {version} could not be parsed. Reverting to v0.800",
            stacklevel=1,
        )
    return StrawberryPlugin
