from typing import Any, Callable, Dict, List, Optional, Set, Tuple, cast

from typing_extensions import Final

from mypy.nodes import (
    ARG_POS,
    GDEF,
    MDEF,
    Argument,
    AssignmentStmt,
    CallExpr,
    CastExpr,
    Context,
    Expression,
    IndexExpr,
    MemberExpr,
    NameExpr,
    PlaceholderNode,
    RefExpr,
    SymbolTableNode,
    TempNode,
    TupleExpr,
    TypeAlias,
    TypeInfo,
    TypeVarExpr,
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
from mypy.plugins.common import _get_decorator_bool_argument, add_method
from mypy.plugins.dataclasses import DataclassAttribute
from mypy.server.trigger import make_wildcard_trigger
from mypy.types import (
    AnyType,
    Instance,
    NoneType,
    Type,
    TypeOfAny,
    TypeVarDef,
    TypeVarType,
    UnionType,
    get_proper_type,
)


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
        return api.named_type_or_none(name)  # type: ignore

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

        return _get_named_type(expr.name, api)

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


def strawberry_pydantic_class_callback(ctx: ClassDefContext):
    # in future we want to have a proper pydantic plugin, but for now
    # let's fallback to any, some resources are here:
    # https://github.com/samuelcolvin/pydantic/blob/master/pydantic/mypy.py
    # >>> model_index = ctx.cls.decorators[0].arg_names.index("model")
    # >>> model_name = ctx.cls.decorators[0].args[model_index].name

    # >>> model_type = ctx.api.named_type("UserModel")
    # >>> model_type = ctx.api.lookup(model_name, Context())

    ctx.cls.info.fallback_to_any = True


def is_dataclasses_field_or_strawberry_field(expr: Expression) -> bool:
    if isinstance(expr, CallExpr):
        if isinstance(expr.callee, RefExpr) and expr.callee.fullname in (
            "dataclasses.field",
            "strawberry.field.field",
            "strawberry.federation.field",
            "strawberry.federation.field.field",
        ):
            return True

        if isinstance(expr.callee, MemberExpr) and isinstance(
            expr.callee.expr, NameExpr
        ):
            return expr.callee.name == "field" and expr.callee.expr.name == "strawberry"

    return False


def _collect_field_args(expr: Expression) -> Tuple[bool, Dict[str, Expression]]:
    """Returns a tuple where the first value represents whether or not
    the expression is a call to dataclass.field and the second is a
    dictionary of the keyword arguments that field() was called with.
    """

    if is_dataclasses_field_or_strawberry_field(expr):
        expr = cast(CallExpr, expr)

        # field() only takes keyword arguments.
        args = {}

        for name, arg in zip(expr.arg_names, expr.args):
            assert name is not None
            args[name] = arg
        return True, args

    return False, {}


# Custom dataclass transformer that knows about strawberry.field, we cannot
# extend the mypy one as it might be compiled by mypyc and we'd get this error
# >>> TypeError: interpreted classes cannot inherit from compiled
# Original copy from
# https://github.com/python/mypy/blob/849a7f73/mypy/plugins/dataclasses.py

SELF_TVAR_NAME = "_DT"  # type: Final


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
            add_method(
                ctx,
                "__init__",
                args=[attr.to_argument() for attr in attributes if attr.is_in_init],
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
                order_other_type = TypeVarType(order_tvar_def)
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

            has_field_call, field_args = _collect_field_args(stmt.rvalue)

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

            # add support for mypy >= 0.800 without breaking backwards compatibility
            # https://github.com/python/mypy/pull/9380/file
            # https://github.com/strawberry-graphql/strawberry/issues/678

            try:
                attribute = DataclassAttribute(**params)  # type: ignore
            except TypeError:
                params["info"] = cls.info
                attribute = DataclassAttribute(**params)  # type: ignore

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
                name = data["name"]  # type: str
                if name not in known_attrs:
                    attr = DataclassAttribute.deserialize(info, data, ctx.api)
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

        # Ensure that arguments without a default don't follow
        # arguments that have a default.
        found_default = False
        for attr in all_attrs:
            # If we find any attribute that is_in_init but that
            # doesn't have a default after one that does have one,
            # then that's an error.
            if found_default and attr.is_in_init and not attr.has_default:
                # If the issue comes from merging different classes, report it
                # at the class definition point.
                context = (
                    Context(line=attr.line, column=attr.column)
                    if attr in attrs
                    else ctx.cls
                )
                ctx.api.fail(
                    "Attributes without a default cannot follow attributes with one",
                    context,
                )

            found_default = found_default or (attr.has_default and attr.is_in_init)

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
                var = attr.to_var()
                var.info = info
                var.is_property = True
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

        if self._is_strawberry_create_type(fullname):
            return create_type_hook

        return None

    def get_function_hook(
        self, fullname: str
    ) -> Optional[Callable[[FunctionContext], Type]]:
        if self._is_strawberry_field(fullname):
            return strawberry_field_hook

        return None

    def get_type_analyze_hook(self, fullname: str):
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
            "strawberry.federation.field",
        }:
            return True

        return any(
            fullname.endswith(decorator)
            for decorator in {
                "strawberry.field",
                "strawberry.federation.field",
            }
        )

    def _is_strawberry_enum(self, fullname: str) -> bool:
        return fullname == "strawberry.enum.enum" or fullname.endswith(
            "strawberry.enum"
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
                "strawberry.schema_directive.schema_directive",
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


def plugin(version: str):
    return StrawberryPlugin
