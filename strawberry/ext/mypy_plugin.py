from __future__ import annotations

import re
import typing
import warnings
from decimal import Decimal
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
    cast,
)

from mypy.nodes import (
    ARG_OPT,
    ARG_POS,
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
    PlaceholderNode,
    RefExpr,
    SymbolTableNode,
    TempNode,
    TupleExpr,
    TypeAlias,
    TypeVarExpr,
    Var,
)
from mypy.plugin import (
    Plugin,
    SemanticAnalyzerPluginInterface,
)
from mypy.plugins.common import _get_argument, _get_decorator_bool_argument, add_method
from mypy.plugins.dataclasses import DataclassAttribute
from mypy.semanal_shared import set_callable_name
from mypy.server.trigger import make_wildcard_trigger
from mypy.types import (
    AnyType,
    CallableType,
    Instance,
    NoneType,
    TypeOfAny,
    TypeVarType,
    UnionType,
    get_proper_type,
)
from mypy.typevars import fill_typevars
from mypy.util import get_unique_redefinition_name

# Backwards compatible with the removal of `TypeVarDef` in mypy 0.920.
try:
    from mypy.types import TypeVarDef  # type: ignore
except ImportError:
    TypeVarDef = TypeVarType

# To be compatible with user who don't use pydantic
try:
    from pydantic.mypy import METADATA_KEY as PYDANTIC_METADATA_KEY
    from pydantic.mypy import PydanticModelField
except ImportError:
    PYDANTIC_METADATA_KEY = ""


if TYPE_CHECKING:
    from typing_extensions import Final

    from mypy.nodes import ClassDef, Expression, TypeInfo
    from mypy.plugins import (  # type: ignore
        AnalyzeTypeContext,
        CheckerPluginInterface,
        ClassDefContext,
        DynamicClassDefContext,
        FunctionContext,
    )
    from mypy.types import Type


VERSION_RE = re.compile(r"(^0|^(?:[1-9][0-9]*))\.(0|(?:[1-9][0-9]*))")
FALLBACK_VERSION = Decimal("0.800")


class MypyVersion:
    """Stores the mypy version to be used by the plugin"""

    VERSION: Decimal


class InvalidNodeTypeException(Exception):
    def __init__(self, node: Any) -> None:
        self.message = f"Invalid node type: {str(node)}"

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


def strawberry_field_hook(ctx: FunctionContext) -> Type:
    # TODO: check when used as decorator, check type of the caller
    # TODO: check type of resolver if any

    return AnyType(TypeOfAny.special_form)


def _get_named_type(name: str, api: SemanticAnalyzerPluginInterface):
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
            for _name, data in model_type.type.metadata[PYDANTIC_METADATA_KEY][
                "fields"
            ].items():
                field = PydanticModelField.deserialize(ctx.cls.info, data)
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
            add_method(
                ctx,
                "to_pydantic",
                args=[
                    f.to_argument(
                        # TODO: use_alias should depend on config?
                        info=model_type.type,
                        typed=True,
                        force_optional=False,
                        use_alias=True,
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

        add_static_method_to_class(
            ctx.api,
            ctx.cls,
            name="from_pydantic",
            args=[model_argument],
            return_type=fill_typevars(ctx.cls.info),
        )


def is_dataclasses_field_or_strawberry_field(expr: Expression) -> bool:
    if isinstance(expr, CallExpr):
        if isinstance(expr.callee, RefExpr) and expr.callee.fullname in (
            "dataclasses.field",
            "strawberry.field.field",
            "strawberry.mutation.mutation",
            "strawberry.federation.field",
            "strawberry.federation.field.field",
        ):
            return True

        if isinstance(expr.callee, MemberExpr) and isinstance(
            expr.callee.expr, NameExpr
        ):
            return (
                expr.callee.name in {"field", "mutation"}
                and expr.callee.expr.name == "strawberry"
            )

    return False


def _collect_field_args(
    ctx: ClassDefContext, expr: Expression
) -> Tuple[bool, Dict[str, Expression]]:
    """Returns a tuple where the first value represents whether or not
    the expression is a call to dataclass.field and the second is a
    dictionary of the keyword arguments that field() was called with.
    """

    if is_dataclasses_field_or_strawberry_field(expr):
        expr = cast(CallExpr, expr)

        args = {}

        for name, arg in zip(expr.arg_names, expr.args):
            if name is None:
                ctx.api.fail(
                    '"field()" or "mutation()" only takes keyword arguments', expr
                )
                return False, {}

            args[name] = arg
        return True, args

    return False, {}


# Custom dataclass transformer that knows about strawberry.field, we cannot
# extend the mypy one as it might be compiled by mypyc and we'd get this error
# >>> TypeError: interpreted classes cannot inherit from compiled
# Original copy from
# https://github.com/python/mypy/blob/5253f7c0/mypy/plugins/dataclasses.py

SELF_TVAR_NAME: Final = "_DT"


class CustomDataclassTransformer:
    def __init__(self, ctx: ClassDefContext) -> None:
        self._ctx = ctx

    def transform(self) -> None:
        """Apply all the necessary transformations to the underlying
        dataclass so as to ensure it is fully type checked according
        to the rules in PEP 557.
        """
        ctx = self._ctx
        info = self._ctx.cls.info
        attributes = self.collect_attributes()
        if attributes is None:
            # Some definitions are not ready, defer() should be already called.
            return
        for attr in attributes:
            if attr.type is None:
                ctx.api.defer()
                return
        decorator_arguments = {
            "init": _get_decorator_bool_argument(self._ctx, "init", True),
            "eq": _get_decorator_bool_argument(self._ctx, "eq", True),
            "order": _get_decorator_bool_argument(self._ctx, "order", False),
            "frozen": _get_decorator_bool_argument(self._ctx, "frozen", False),
        }

        # If there are no attributes, it may be that the semantic analyzer has not
        # processed them yet. In order to work around this, we can simply skip
        # generating __init__ if there are no attributes, because if the user
        # truly did not define any, then the object default __init__ with an
        # empty signature will be present anyway.
        if (
            decorator_arguments["init"]
            and (
                "__init__" not in info.names or info.names["__init__"].plugin_generated
            )
            and attributes
        ):
            args = [info] if MypyVersion.VERSION >= Decimal("1.0") else []

            add_method(
                ctx,
                "__init__",
                args=[
                    attr.to_argument(*args) for attr in attributes if attr.is_in_init
                ],
                return_type=NoneType(),
            )

        if (
            decorator_arguments["eq"]
            and info.get("__eq__") is None
            or decorator_arguments["order"]
        ):
            # Type variable for self types in generated methods.
            obj_type = ctx.api.named_type("__builtins__.object")
            self_tvar_expr = TypeVarExpr(
                SELF_TVAR_NAME, info.fullname + "." + SELF_TVAR_NAME, [], obj_type
            )
            info.names[SELF_TVAR_NAME] = SymbolTableNode(MDEF, self_tvar_expr)

        # Add <, >, <=, >=, but only if the class has an eq method.
        if decorator_arguments["order"]:
            if not decorator_arguments["eq"]:
                ctx.api.fail("eq must be True if order is True", ctx.cls)

            for method_name in ["__lt__", "__gt__", "__le__", "__ge__"]:
                # Like for __eq__ and __ne__, we want "other" to match
                # the self type.
                obj_type = ctx.api.named_type("__builtins__.object")
                order_tvar_def = TypeVarDef(
                    SELF_TVAR_NAME,
                    info.fullname + "." + SELF_TVAR_NAME,
                    -1,
                    [],
                    obj_type,
                )

                # Backwards compatible with the removal of `TypeVarDef` in mypy 0.920.
                if isinstance(order_tvar_def, TypeVarType):
                    order_other_type = order_tvar_def
                else:
                    order_other_type = TypeVarType(order_tvar_def)  # type: ignore

                order_return_type = ctx.api.named_type("__builtins__.bool")
                order_args = [
                    Argument(
                        Var("other", order_other_type), order_other_type, None, ARG_POS
                    )
                ]

                existing_method = info.get(method_name)
                if existing_method is not None and not existing_method.plugin_generated:
                    assert existing_method.node
                    ctx.api.fail(
                        "You may not have a custom %s method when order=True"
                        % method_name,
                        existing_method.node,
                    )

                add_method(
                    ctx,
                    method_name,
                    args=order_args,
                    return_type=order_return_type,
                    self_type=order_other_type,
                    tvar_def=order_tvar_def,
                )

        if decorator_arguments["frozen"]:
            self._freeze(attributes)
        else:
            self._propertize_callables(attributes)

        self.reset_init_only_vars(info, attributes)

        info.metadata["dataclass"] = {
            "attributes": [attr.serialize() for attr in attributes],
            "frozen": decorator_arguments["frozen"],
        }

    def reset_init_only_vars(
        self, info: TypeInfo, attributes: List[DataclassAttribute]
    ) -> None:
        """Remove init-only vars from the class and reset init var declarations."""
        for attr in attributes:
            if attr.is_init_var:
                if attr.name in info.names:
                    del info.names[attr.name]
                else:
                    # Nodes of superclass InitVars not used in __init__
                    # cannot be reached.
                    assert attr.is_init_var
                for stmt in info.defn.defs.body:
                    if isinstance(stmt, AssignmentStmt) and stmt.unanalyzed_type:
                        lvalue = stmt.lvalues[0]
                        if isinstance(lvalue, NameExpr) and lvalue.name == attr.name:
                            # Reset node so that another semantic analysis pass will
                            # recreate a symbol node for this attribute.
                            lvalue.node = None

    def collect_attributes(self) -> Optional[List[DataclassAttribute]]:
        """Collect all attributes declared in the dataclass and its parents.
        All assignments of the form
            a: SomeType
            b: SomeOtherType = ...
        are collected.
        """

        # First, collect attributes belonging to the current class.
        ctx = self._ctx
        cls = self._ctx.cls
        attrs: List[DataclassAttribute] = []
        known_attrs: Set[str] = set()
        for stmt in cls.defs.body:
            # Any assignment that doesn't use the new type declaration
            # syntax can be ignored out of hand.
            if not (isinstance(stmt, AssignmentStmt) and stmt.new_syntax):
                continue

            # a: int, b: str = 1, 'foo' is not supported syntax so we
            # don't have to worry about it.
            lhs = stmt.lvalues[0]
            if not isinstance(lhs, NameExpr):
                continue

            sym = cls.info.names.get(lhs.name)
            if sym is None:
                # This name is likely blocked by a star import. We don't need
                # to defer because defer() is already called by mark_incomplete().
                continue

            node = sym.node
            if isinstance(node, PlaceholderNode):
                # This node is not ready yet.
                return None
            assert isinstance(node, Var)

            # x: ClassVar[int] is ignored by dataclasses.
            if node.is_classvar:
                continue

            # x: InitVar[int] is turned into x: int and is removed from the class.
            is_init_var = False
            node_type = get_proper_type(node.type)
            if (
                isinstance(node_type, Instance)
                and node_type.type.fullname == "dataclasses.InitVar"
            ):
                is_init_var = True
                node.type = node_type.args[0]

            has_field_call, field_args = _collect_field_args(ctx, stmt.rvalue)

            is_in_init_param = field_args.get("init")
            if is_in_init_param is None:
                is_in_init = True
            else:
                is_in_init = bool(ctx.api.parse_bool(is_in_init_param))

            # fields with a resolver are never put in the __init__ method
            if "resolver" in field_args:
                is_in_init = False

            has_default = False
            # Ensure that something like x: int = field() is rejected
            # after an attribute with a default.
            if has_field_call:
                has_default = "default" in field_args or "default_factory" in field_args

            # All other assignments are already type checked.
            elif not isinstance(stmt.rvalue, TempNode):
                has_default = True

            if not has_default:
                # Make all non-default attributes implicit because they are de-facto set
                # on self in the generated __init__(), not in the class body.
                sym.implicit = True

            known_attrs.add(lhs.name)
            params = dict(
                name=lhs.name,
                is_in_init=is_in_init,
                is_init_var=is_init_var,
                has_default=has_default,
                line=stmt.line,
                column=stmt.column,
                type=sym.type,
            )

            # Support the addition of `info` in mypy 0.800 and `kw_only` in mypy 0.920
            # without breaking backwards compatibility.
            if MypyVersion.VERSION >= Decimal("0.800"):
                params["info"] = cls.info
            if MypyVersion.VERSION >= Decimal("0.920"):
                params["kw_only"] = True
            if MypyVersion.VERSION >= Decimal("1.1"):
                params["alias"] = None

            attribute = DataclassAttribute(**params)
            attrs.append(attribute)

        # Next, collect attributes belonging to any class in the MRO
        # as long as those attributes weren't already collected.  This
        # makes it possible to overwrite attributes in subclasses.
        # copy() because we potentially modify all_attrs below and if
        # this code requires debugging we'll have unmodified attrs laying around.
        all_attrs = attrs.copy()
        for info in cls.info.mro[1:-1]:
            if "dataclass" not in info.metadata:
                continue

            super_attrs = []
            # Each class depends on the set of attributes in its dataclass ancestors.
            ctx.api.add_plugin_dependency(make_wildcard_trigger(info.fullname))

            for data in info.metadata["dataclass"]["attributes"]:
                name: str = data["name"]
                if name not in known_attrs:
                    attr = DataclassAttribute.deserialize(info, data, ctx.api)
                    attr.expand_typevar_from_subtype(ctx.cls.info)
                    known_attrs.add(name)
                    super_attrs.append(attr)
                elif all_attrs:
                    # How early in the attribute list an attribute appears is
                    # determined by the reverse MRO, not simply MRO.
                    # See https://docs.python.org/3/library/dataclasses.html#inheritance
                    # for details.
                    for attr in all_attrs:
                        if attr.name == name:
                            all_attrs.remove(attr)
                            super_attrs.append(attr)
                            break
            all_attrs = super_attrs + all_attrs

        return all_attrs

    def _freeze(self, attributes: List[DataclassAttribute]) -> None:
        """Converts all attributes to @property methods in order to
        emulate frozen classes.
        """
        info = self._ctx.cls.info
        for attr in attributes:
            sym_node = info.names.get(attr.name)
            if sym_node is not None:
                var = sym_node.node
                assert isinstance(var, Var)
                var.is_property = True
            else:
                if MypyVersion.VERSION >= Decimal("1.0"):
                    var = attr.to_var(current_info=info)
                else:
                    var = attr.to_var()  # type: ignore
                    var.info = info

                var.is_property = True
                var._fullname = info.fullname + "." + var.name
                info.names[var.name] = SymbolTableNode(MDEF, var)

    def _propertize_callables(self, attributes: List[DataclassAttribute]) -> None:
        """Converts all attributes with callable types to @property methods.

        This avoids the typechecker getting confused and thinking that
        `my_dataclass_instance.callable_attr(foo)` is going to receive a
        `self` argument (it is not).

        """
        info = self._ctx.cls.info
        for attr in attributes:
            if isinstance(get_proper_type(attr.type), CallableType):
                if MypyVersion.VERSION >= Decimal("1.0"):
                    var = attr.to_var(current_info=info)
                else:
                    var = attr.to_var()  # type: ignore
                    var.info = info

                var.is_property = True
                var.is_settable_property = True
                var._fullname = info.fullname + "." + var.name
                info.names[var.name] = SymbolTableNode(MDEF, var)


def custom_dataclass_class_maker_callback(ctx: ClassDefContext) -> None:
    """Hooks into the class typechecking process to add support for dataclasses."""
    transformer = CustomDataclassTransformer(ctx)
    transformer.transform()


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

    def get_function_hook(
        self, fullname: str
    ) -> Optional[Callable[[FunctionContext], Type]]:
        if self._is_strawberry_field(fullname):
            return strawberry_field_hook

        return None

    def get_type_analyze_hook(self, fullname: str) -> Union[Callable[..., Type], None]:
        if self._is_strawberry_lazy_type(fullname):
            return lazy_type_analyze_callback

        return None

    def get_class_decorator_hook(
        self, fullname: str
    ) -> Optional[Callable[[ClassDefContext], None]]:
        if self._is_strawberry_decorator(fullname):
            return custom_dataclass_class_maker_callback

        if self._is_strawberry_pydantic_decorator(fullname):
            return strawberry_pydantic_class_callback

        return None

    def _is_strawberry_union(self, fullname: str) -> bool:
        return fullname == "strawberry.union.union" or fullname.endswith(
            "strawberry.union"
        )

    def _is_strawberry_field(self, fullname: str) -> bool:
        if fullname in {
            "strawberry.field.field",
            "strawberry.mutation.mutation",
            "strawberry.federation.field",
        }:
            return True

        return any(
            fullname.endswith(decorator)
            for decorator in {
                "strawberry.field",
                "strawberry.mutation",
                "strawberry.federation.field",
            }
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

    def _is_strawberry_decorator(self, fullname: str) -> bool:
        if any(
            strawberry_decorator in fullname
            for strawberry_decorator in {
                "strawberry.object_type.type",
                "strawberry.federation.type",
                "strawberry.federation.object_type.type",
                "strawberry.federation.input",
                "strawberry.federation.object_type.input",
                "strawberry.federation.interface",
                "strawberry.federation.object_type.interface",
                "strawberry.schema_directive.schema_directive",
                "strawberry.federation.schema_directive",
                "strawberry.federation.schema_directive.schema_directive",
                "strawberry.object_type.input",
                "strawberry.object_type.interface",
            }
        ):
            return True

        # in some cases `fullpath` is not what we would expect, this usually
        # happens when `follow_imports` are disabled in mypy when you get a path
        # that looks likes `some_module.types.strawberry.type`

        return any(
            fullname.endswith(decorator)
            for decorator in {
                "strawberry.type",
                "strawberry.federation.type",
                "strawberry.input",
                "strawberry.interface",
                "strawberry.schema_directive",
                "strawberry.federation.schema_directive",
            }
        )

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
            for strawberry_decorator in {
                "strawberry.experimental.pydantic.object_type.type",
                "strawberry.experimental.pydantic.object_type.input",
                "strawberry.experimental.pydantic.object_type.interface",
                "strawberry.experimental.pydantic.error_type",
            }
        ):
            return True

        # in some cases `fullpath` is not what we would expect, this usually
        # happens when `follow_imports` are disabled in mypy when you get a path
        # that looks likes `some_module.types.strawberry.type`

        return any(
            fullname.endswith(decorator)
            for decorator in {
                "strawberry.experimental.pydantic.type",
                "strawberry.experimental.pydantic.input",
                "strawberry.experimental.pydantic.error_type",
            }
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
