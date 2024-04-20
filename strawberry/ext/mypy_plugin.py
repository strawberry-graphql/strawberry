from __future__ import annotations

import re
import typing
import warnings
from decimal import Decimal
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    List,
    Optional,
    Set,
    Tuple,
    Union,
    cast,
)

from mypy.nodes import (
    ARG_OPT,
    ARG_STAR2,
    GDEF,
    MDEF,
    Argument,
    AssignmentStmt,
    Block,
    CallExpr,
    CastExpr,
    FuncDef,
    IndexExpr,
    MemberExpr,
    NameExpr,
    PassStmt,
    SymbolTableNode,
    TupleExpr,
    TypeAlias,
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
    TypeOfAny,
    TypeVarType,
    UnionType,
)
from mypy.typevars import fill_typevars
from mypy.util import get_unique_redefinition_name

# Backwards compatible with the removal of `TypeVarDef` in mypy 0.920.
try:
    from mypy.types import TypeVarDef  # type: ignore
except ImportError:
    TypeVarDef = TypeVarType

PYDANTIC_VERSION: Optional[Tuple[int, ...]] = None

# To be compatible with user who don't use pydantic
try:
    import pydantic
    from pydantic.mypy import METADATA_KEY as PYDANTIC_METADATA_KEY
    from pydantic.mypy import PydanticModelField

    PYDANTIC_VERSION = tuple(map(int, pydantic.__version__.split(".")))

    from strawberry.experimental.pydantic._compat import IS_PYDANTIC_V1
except ImportError:
    PYDANTIC_METADATA_KEY = ""
    IS_PYDANTIC_V1 = False


if TYPE_CHECKING:
    from mypy.nodes import ClassDef, Expression
    from mypy.plugins import (  # type: ignore
        AnalyzeTypeContext,
        CheckerPluginInterface,
        ClassDefContext,
        DynamicClassDefContext,
    )
    from mypy.types import Type


VERSION_RE = re.compile(r"(^0|^(?:[1-9][0-9]*))\.(0|(?:[1-9][0-9]*))")
FALLBACK_VERSION = Decimal("0.800")


class MypyVersion:
    """Stores the mypy version to be used by the plugin"""

    VERSION: Decimal


class InvalidNodeTypeException(Exception):
    def __init__(self, node: Any) -> None:
        self.message = f"Invalid node type: {node!s}"

        super().__init__()

    def __str__(self) -> str:
        return self.message


def lazy_type_analyze_callback(ctx: AnalyzeTypeContext) -> Type:
    if len(ctx.type.args) == 0:
        # TODO: maybe this should throw an error

        return AnyType(TypeOfAny.special_form)

    type_name = ctx.type.args[0]
    type_ = ctx.api.analyze_type(type_name)

    return type_


def _get_named_type(name: str, api: SemanticAnalyzerPluginInterface) -> Any:
    if "." in name:
        return api.named_type_or_none(name)

    return api.named_type(name)


def _get_type_for_expr(expr: Expression, api: SemanticAnalyzerPluginInterface) -> Type:
    if isinstance(expr, NameExpr):
        # guarding against invalid nodes, still have to figure out why this happens
        # but sometimes mypy crashes because the internal node of the named type
        # is actually a Var node, which is unexpected, so we do a naive guard here
        # and raise an exception for it.

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
        else:
            raise InvalidNodeTypeException(expr)

    if isinstance(expr, CallExpr):
        if expr.analyzed:
            return _get_type_for_expr(expr.analyzed, api)
        else:
            raise InvalidNodeTypeException(expr)

    if isinstance(expr, CastExpr):
        return expr.type

    raise ValueError(f"Unsupported expression {type(expr)}")


def create_type_hook(ctx: DynamicClassDefContext) -> None:
    # returning classes/type aliases is not supported yet by mypy
    # see https://github.com/python/mypy/issues/5865

    type_alias = TypeAlias(
        AnyType(TypeOfAny.from_error),
        fullname=ctx.api.qualified_name(ctx.name),
        line=ctx.call.line,
        column=ctx.call.column,
    )

    ctx.api.add_symbol_table_node(
        ctx.name,
        SymbolTableNode(GDEF, type_alias, plugin_generated=True),
    )

    return


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

    enum_type: Optional[Type]

    try:
        enum_type = _get_type_for_expr(first_argument, ctx.api)
    except InvalidNodeTypeException:
        enum_type = None

    if not enum_type:
        enum_type = AnyType(TypeOfAny.from_error)

    type_alias = TypeAlias(
        enum_type,
        fullname=ctx.api.qualified_name(ctx.name),
        line=ctx.call.line,
        column=ctx.call.column,
    )

    ctx.api.add_symbol_table_node(
        ctx.name, SymbolTableNode(GDEF, type_alias, plugin_generated=False)
    )


def scalar_hook(ctx: DynamicClassDefContext) -> None:
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

    scalar_type: Optional[Type]

    # TODO: add proper support for NewType

    try:
        scalar_type = _get_type_for_expr(first_argument, ctx.api)
    except InvalidNodeTypeException:
        scalar_type = None

    if not scalar_type:
        scalar_type = AnyType(TypeOfAny.from_error)

    type_alias = TypeAlias(
        scalar_type,
        fullname=ctx.api.qualified_name(ctx.name),
        line=ctx.call.line,
        column=ctx.call.column,
    )

    ctx.api.add_symbol_table_node(
        ctx.name, SymbolTableNode(GDEF, type_alias, plugin_generated=False)
    )


def add_static_method_to_class(
    api: Union[SemanticAnalyzerPluginInterface, CheckerPluginInterface],
    cls: ClassDef,
    name: str,
    args: List[Argument],
    return_type: Type,
    tvar_def: Optional[TypeVarType] = None,
) -> None:
    """Adds a static method
    Edited add_method_to_class to incorporate static method logic
    https://github.com/python/mypy/blob/9c05d3d19/mypy/plugins/common.py
    """
    info = cls.info

    # First remove any previously generated methods with the same name
    # to avoid clashes and problems in the semantic analyzer.
    if name in info.names:
        sym = info.names[name]
        if sym.plugin_generated and isinstance(sym.node, FuncDef):
            cls.defs.body.remove(sym.node)

    # For compat with mypy < 0.93
    if MypyVersion.VERSION < Decimal("0.93"):
        function_type = api.named_type("__builtins__.function")
    else:
        if isinstance(api, SemanticAnalyzerPluginInterface):
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
        signature.variables = [tvar_def]

    func = FuncDef(name, args, Block([PassStmt()]))

    func.is_static = True
    func.info = info
    func.type = set_callable_name(signature, func)
    func._fullname = f"{info.fullname}.{name}"
    func.line = info.line

    # NOTE: we would like the plugin generated node to dominate, but we still
    # need to keep any existing definitions so they get semantically analyzed.
    if name in info.names:
        # Get a nice unique name instead.
        r_name = get_unique_redefinition_name(name, info.names)
        info.names[r_name] = info.names[name]

    info.names[name] = SymbolTableNode(MDEF, func, plugin_generated=True)
    info.defn.defs.body.append(func)


def strawberry_pydantic_class_callback(ctx: ClassDefContext) -> None:
    # in future we want to have a proper pydantic plugin, but for now
    # let's fallback to **kwargs for __init__, some resources are here:
    # https://github.com/samuelcolvin/pydantic/blob/master/pydantic/mypy.py
    # >>> model_index = ctx.cls.decorators[0].arg_names.index("model")
    # >>> model_name = ctx.cls.decorators[0].args[model_index].name

    # >>> model_type = ctx.api.named_type("UserModel")
    # >>> model_type = ctx.api.lookup(model_name, Context())

    model_expression = _get_argument(call=ctx.reason, name="model")
    if model_expression is None:
        ctx.api.fail("model argument in decorator failed to be parsed", ctx.reason)

    else:
        # Add __init__
        init_args = [
            Argument(Var("kwargs"), AnyType(TypeOfAny.explicit), None, ARG_STAR2)
        ]
        add_method(ctx, "__init__", init_args, NoneType())

        model_type = cast(Instance, _get_type_for_expr(model_expression, ctx.api))

        # these are the fields that the user added to the strawberry type
        new_strawberry_fields: Set[str] = set()

        # TODO: think about inheritance for strawberry?
        for stmt in ctx.cls.defs.body:
            if isinstance(stmt, AssignmentStmt):
                lhs = cast(NameExpr, stmt.lvalues[0])
                new_strawberry_fields.add(lhs.name)

        pydantic_fields: Set[PydanticModelField] = set()
        try:
            fields = model_type.type.metadata[PYDANTIC_METADATA_KEY]["fields"]
            for data in fields.items():
                if IS_PYDANTIC_V1:
                    field = PydanticModelField.deserialize(ctx.cls.info, data[1])  # type:ignore[call-arg]
                else:
                    field = PydanticModelField.deserialize(
                        info=ctx.cls.info, data=data[1], api=ctx.api
                    )
                pydantic_fields.add(field)
        except KeyError:
            # this will happen if the user didn't add the pydantic plugin
            # AND is using the pydantic conversion decorator
            ctx.api.fail(
                "Pydantic plugin not installed,"
                " please add pydantic.mypy your mypy.ini plugins",
                ctx.reason,
            )

        potentially_missing_fields: Set[PydanticModelField] = {
            f for f in pydantic_fields if f.name not in new_strawberry_fields
        }

        """
        Need to check if all_fields=True from the pydantic decorator
        There is no way to real check that Literal[True] was used
        We just check if the strawberry type is missing all the fields
        This means that the user is using all_fields=True
        """
        is_all_fields: bool = len(potentially_missing_fields) == len(pydantic_fields)
        missing_pydantic_fields: Set[PydanticModelField] = (
            potentially_missing_fields if not is_all_fields else set()
        )

        # Add the default to_pydantic if undefined by the user
        if "to_pydantic" not in ctx.cls.info.names:
            if IS_PYDANTIC_V1:
                add_method(
                    ctx,
                    "to_pydantic",
                    args=[
                        f.to_argument(
                            # TODO: use_alias should depend on config?
                            info=model_type.type,  # type:ignore[call-arg]
                            typed=True,
                            force_optional=False,
                            use_alias=True,
                        )
                        for f in missing_pydantic_fields
                    ],
                    return_type=model_type,
                )
            else:
                extra = {}

                if PYDANTIC_VERSION and PYDANTIC_VERSION >= (2, 7, 0):
                    extra["api"] = ctx.api

                add_method(
                    ctx,
                    "to_pydantic",
                    args=[
                        f.to_argument(
                            # TODO: use_alias should depend on config?
                            current_info=model_type.type,
                            typed=True,
                            force_optional=False,
                            use_alias=True,
                            **extra,
                        )
                        for f in missing_pydantic_fields
                    ],
                    return_type=model_type,
                )

        # Add from_pydantic
        model_argument = Argument(
            variable=Var(name="instance", type=model_type),
            type_annotation=model_type,
            initializer=None,
            kind=ARG_OPT,
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


class StrawberryPlugin(Plugin):
    def get_dynamic_class_hook(
        self, fullname: str
    ) -> Optional[Callable[[DynamicClassDefContext], None]]:
        # TODO: investigate why we need this instead of `strawberry.union.union` on CI
        # we have the same issue in the other hooks
        if self._is_strawberry_union(fullname):
            return union_hook

        if self._is_strawberry_enum(fullname):
            return enum_hook

        if self._is_strawberry_scalar(fullname):
            return scalar_hook

        if self._is_strawberry_create_type(fullname):
            return create_type_hook

        return None

    def get_type_analyze_hook(self, fullname: str) -> Union[Callable[..., Type], None]:
        if self._is_strawberry_lazy_type(fullname):
            return lazy_type_analyze_callback

        return None

    def get_class_decorator_hook(
        self, fullname: str
    ) -> Optional[Callable[[ClassDefContext], None]]:
        if self._is_strawberry_pydantic_decorator(fullname):
            return strawberry_pydantic_class_callback

        return None

    def _is_strawberry_union(self, fullname: str) -> bool:
        return fullname == "strawberry.union.union" or fullname.endswith(
            "strawberry.union"
        )

    def _is_strawberry_enum(self, fullname: str) -> bool:
        return fullname == "strawberry.enum.enum" or fullname.endswith(
            "strawberry.enum"
        )

    def _is_strawberry_scalar(self, fullname: str) -> bool:
        return fullname == "strawberry.custom_scalar.scalar" or fullname.endswith(
            "strawberry.scalar"
        )

    def _is_strawberry_lazy_type(self, fullname: str) -> bool:
        return fullname == "strawberry.lazy_type.LazyType"

    def _is_strawberry_create_type(self, fullname: str) -> bool:
        # using endswith(.create_type) is not ideal as there might be
        # other function called like that, but it's the best we can do
        # when follow-imports is set to "skip". Hopefully in the future
        # we can remove our custom hook for create type

        return (
            fullname == "strawberry.tools.create_type.create_type"
            or fullname.endswith(".create_type")
        )

    def _is_strawberry_pydantic_decorator(self, fullname: str) -> bool:
        if any(
            strawberry_decorator in fullname
            for strawberry_decorator in (
                "strawberry.experimental.pydantic.object_type.type",
                "strawberry.experimental.pydantic.object_type.input",
                "strawberry.experimental.pydantic.object_type.interface",
                "strawberry.experimental.pydantic.error_type",
            )
        ):
            return True

        # in some cases `fullpath` is not what we would expect, this usually
        # happens when `follow_imports` are disabled in mypy when you get a path
        # that looks likes `some_module.types.strawberry.type`

        return any(
            fullname.endswith(decorator)
            for decorator in (
                "strawberry.experimental.pydantic.type",
                "strawberry.experimental.pydantic.input",
                "strawberry.experimental.pydantic.error_type",
            )
        )


def plugin(version: str) -> typing.Type[StrawberryPlugin]:
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
