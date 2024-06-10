import ast
import dataclasses
import sys
import typing
from functools import lru_cache
from typing import (  # type: ignore
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    ClassVar,
    Dict,
    ForwardRef,
    Generic,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    _eval_type,
    _GenericAlias,
    _SpecialForm,
    cast,
    overload,
)
from typing_extensions import Annotated, TypeGuard, get_args, get_origin

ast_unparse = getattr(ast, "unparse", None)
# ast.unparse is only available on python 3.9+. For older versions we will
# use `astunparse.unparse`.
# We are also using "not TYPE_CHECKING" here because mypy gives an erorr
# on tests because "astunparse" is missing stubs, but the mypy action says
# that the comment is unused.
if not TYPE_CHECKING and ast_unparse is None:
    import astunparse

    ast_unparse = astunparse.unparse


@lru_cache
def get_generic_alias(type_: Type) -> Type:
    """Get the generic alias for a type.

    Given a type, its generic alias from `typing` module will be returned
    if it exists. For example:

        >>> get_generic_alias(list)
        typing.List
        >>> get_generic_alias(dict)
        typing.Dict

    This is mostly useful for python versions prior to 3.9, to get a version
    of a concrete type which supports `__class_getitem__`. In 3.9+ types like
    `list`/`dict`/etc are subscriptable and can be used directly instead
    of their generic alias version.
    """
    if isinstance(type_, _SpecialForm):
        return type_

    for attr_name in dir(typing):
        # ignore private attributes, they are not Generic aliases
        if attr_name.startswith("_"):  # pragma: no cover
            continue

        attr = getattr(typing, attr_name)
        if is_generic_alias(attr) and attr.__origin__ is type_:
            return attr

    raise AssertionError(f"No GenericAlias available for {type_}")  # pragma: no cover


def is_generic_alias(type_: Any) -> TypeGuard[_GenericAlias]:
    """Returns True if the type is a generic alias."""
    # _GenericAlias overrides all the methods that we can use to know if
    # this is a subclass of it. But if it has an "_inst" attribute
    # then it for sure is a _GenericAlias
    return hasattr(type_, "_inst")


def is_list(annotation: object) -> bool:
    """Returns True if annotation is a List"""

    annotation_origin = getattr(annotation, "__origin__", None)

    return annotation_origin == list


def is_union(annotation: object) -> bool:
    """Returns True if annotation is a Union"""

    # this check is needed because unions declared with the new syntax `A | B`
    # don't have a `__origin__` property on them, but they are instances of
    # `UnionType`, which is only available in Python 3.10+
    if sys.version_info >= (3, 10):
        from types import UnionType

        if isinstance(annotation, UnionType):
            return True

    # unions declared as Union[A, B] fall through to this check, even on python 3.10+

    annotation_origin = getattr(annotation, "__origin__", None)

    return annotation_origin == Union


def is_optional(annotation: Type) -> bool:
    """Returns True if the annotation is Optional[SomeType]"""

    # Optionals are represented as unions

    if not is_union(annotation):
        return False

    types = annotation.__args__

    # A Union to be optional needs to have at least one None type
    return any(x == None.__class__ for x in types)


def get_optional_annotation(annotation: Type) -> Type:
    types = annotation.__args__

    non_none_types = tuple(x for x in types if x != None.__class__)

    # if we have multiple non none types we want to return a copy of this
    # type (normally a Union type).

    if len(non_none_types) > 1:
        return annotation.copy_with(non_none_types)

    return non_none_types[0]


def get_list_annotation(annotation: Type) -> Type:
    return annotation.__args__[0]


def is_concrete_generic(annotation: type) -> bool:
    ignored_generics = (list, tuple, Union, ClassVar, AsyncGenerator)
    return (
        isinstance(annotation, _GenericAlias)
        and annotation.__origin__ not in ignored_generics
    )


def is_generic_subclass(annotation: type) -> bool:
    return isinstance(annotation, type) and issubclass(
        annotation,
        Generic,  # type:ignore
    )


def is_generic(annotation: type) -> bool:
    """Returns True if the annotation is or extends a generic."""

    return (
        # TODO: These two lines appear to have the same effect. When will an
        #       annotation have parameters but not satisfy the first condition?
        (is_generic_subclass(annotation) or is_concrete_generic(annotation))
        and bool(get_parameters(annotation))
    )


def is_type_var(annotation: Type) -> bool:
    """Returns True if the annotation is a TypeVar."""

    return isinstance(annotation, TypeVar)


def is_classvar(cls: type, annotation: Union[ForwardRef, str]) -> bool:
    """Returns True if the annotation is a ClassVar."""
    # This code was copied from the dataclassses cpython implementation to check
    # if a field is annotated with ClassVar or not, taking future annotations
    # in consideration.
    if dataclasses._is_classvar(annotation, typing):  # type: ignore
        return True

    annotation_str = (
        annotation.__forward_arg__ if isinstance(annotation, ForwardRef) else annotation
    )
    return isinstance(annotation_str, str) and dataclasses._is_type(  # type: ignore
        annotation_str,
        cls,
        typing,
        typing.ClassVar,
        dataclasses._is_classvar,  # type: ignore
    )


def type_has_annotation(type_: object, annotation: Type) -> bool:
    """Returns True if the type_ has been annotated with annotation."""
    if get_origin(type_) is Annotated:
        return any(isinstance(argument, annotation) for argument in get_args(type_))

    return False


def get_parameters(annotation: Type) -> Union[Tuple[object], Tuple[()]]:
    if (
        isinstance(annotation, _GenericAlias)
        or isinstance(annotation, type)
        and issubclass(annotation, Generic)  # type:ignore
        and annotation is not Generic
    ):
        return annotation.__parameters__
    else:
        return ()  # pragma: no cover


@overload
def _ast_replace_union_operation(expr: ast.expr) -> ast.expr: ...


@overload
def _ast_replace_union_operation(expr: ast.Expr) -> ast.Expr: ...


def _ast_replace_union_operation(
    expr: Union[ast.Expr, ast.expr],
) -> Union[ast.Expr, ast.expr]:
    if isinstance(expr, ast.Expr) and isinstance(
        expr.value, (ast.BinOp, ast.Subscript)
    ):
        expr = ast.Expr(_ast_replace_union_operation(expr.value))
    elif isinstance(expr, ast.BinOp):
        left = _ast_replace_union_operation(expr.left)
        right = _ast_replace_union_operation(expr.right)
        expr = ast.Subscript(
            ast.Name(id="Union"),
            ast.Tuple([left, right], ast.Load()),
            ast.Load(),
        )
    elif isinstance(expr, ast.Tuple):
        expr = ast.Tuple(
            [_ast_replace_union_operation(elt) for elt in expr.elts],
            ast.Load(),
        )
    elif isinstance(expr, ast.Subscript):
        if hasattr(ast, "Index") and isinstance(expr.slice, ast.Index):
            expr = ast.Subscript(
                expr.value,
                # The cast is required for mypy on python 3.7 and 3.8
                ast.Index(_ast_replace_union_operation(cast(Any, expr.slice).value)),
                ast.Load(),
            )
        elif isinstance(expr.slice, (ast.BinOp, ast.Tuple)):
            expr = ast.Subscript(
                expr.value,
                _ast_replace_union_operation(expr.slice),
                ast.Load(),
            )

    return expr


def _get_namespace_from_ast(
    expr: Union[ast.Expr, ast.expr],
    globalns: Optional[Dict] = None,
    localns: Optional[Dict] = None,
) -> Dict[str, Type]:
    from strawberry.lazy_type import StrawberryLazyReference

    extra = {}

    if isinstance(expr, ast.Expr) and isinstance(
        expr.value, (ast.BinOp, ast.Subscript)
    ):
        extra.update(_get_namespace_from_ast(expr.value, globalns, localns))
    elif isinstance(expr, ast.BinOp):
        for elt in (expr.left, expr.right):
            extra.update(_get_namespace_from_ast(elt, globalns, localns))
    elif (
        isinstance(expr, ast.Subscript)
        and isinstance(expr.value, ast.Name)
        and expr.value.id == "Union"
    ):
        if hasattr(ast, "Index") and isinstance(expr.slice, ast.Index):
            # The cast is required for mypy on python 3.7 and 3.8
            expr_slice = cast(Any, expr.slice).value
        else:
            expr_slice = expr.slice

        for elt in cast(ast.Tuple, expr_slice).elts:
            extra.update(_get_namespace_from_ast(elt, globalns, localns))
    elif (
        isinstance(expr, ast.Subscript)
        and isinstance(expr.value, ast.Name)
        and expr.value.id in {"list", "List"}
    ):
        extra.update(_get_namespace_from_ast(expr.slice, globalns, localns))
    elif (
        isinstance(expr, ast.Subscript)
        and isinstance(expr.value, ast.Name)
        and expr.value.id == "Annotated"
    ):
        assert ast_unparse

        if hasattr(ast, "Index") and isinstance(expr.slice, ast.Index):
            # The cast is required for mypy on python 3.7 and 3.8
            expr_slice = cast(Any, expr.slice).value
        else:
            expr_slice = expr.slice

        args: List[str] = []
        for elt in cast(ast.Tuple, expr_slice).elts:
            extra.update(_get_namespace_from_ast(elt, globalns, localns))
            args.append(ast_unparse(elt))

        # When using forward refs, the whole
        # Annotated[SomeType, strawberry.lazy("type.module")] is a forward ref,
        # and trying to _eval_type on it will fail. Take a different approach
        # here to resolve lazy types by execing the annotated args, resolving the
        # type directly and then adding it to extra namespace, so that _eval_type
        # can properly resolve it later
        type_name = args[0].strip(" '\"\n")
        for arg in args[1:]:
            evaled_arg = eval(arg, globalns, localns)  # noqa: PGH001, S307
            if isinstance(evaled_arg, StrawberryLazyReference):
                extra[type_name] = evaled_arg.resolve_forward_ref(ForwardRef(type_name))

    return extra


def eval_type(
    type_: Any,
    globalns: Optional[Dict] = None,
    localns: Optional[Dict] = None,
) -> Type:
    """Evaluates a type, resolving forward references."""
    from strawberry.auto import StrawberryAuto
    from strawberry.lazy_type import StrawberryLazyReference
    from strawberry.private import StrawberryPrivate

    globalns = globalns or {}
    # If this is not a string, maybe its args are (e.g. List["Foo"])
    if isinstance(type_, ForwardRef):
        ast_obj = cast(ast.Expr, ast.parse(type_.__forward_arg__).body[0])

        # For Python 3.10+, we can use the built-in _eval_type function directly.
        # It will handle "|" notations properly
        if sys.version_info < (3, 10):
            ast_obj = _ast_replace_union_operation(ast_obj)

            # We replaced "a | b" with "Union[a, b], so make sure Union can be resolved
            # at globalns because it may not be there
            if "Union" not in globalns:
                globalns["Union"] = Union

        globalns.update(_get_namespace_from_ast(ast_obj, globalns, localns))

        assert ast_unparse
        type_ = ForwardRef(ast_unparse(ast_obj))

        return _eval_type(type_, globalns, localns)

    origin = get_origin(type_)
    if origin is not None:
        args = get_args(type_)
        if origin is Annotated:
            for arg in args[1:]:
                if isinstance(arg, StrawberryPrivate):
                    return type_

                if isinstance(arg, StrawberryLazyReference):
                    remaining_args = [
                        a
                        for a in args[1:]
                        if not isinstance(a, StrawberryLazyReference)
                    ]
                    type_arg = (
                        arg.resolve_forward_ref(args[0])
                        if isinstance(args[0], ForwardRef)
                        else args[0]
                    )
                    args = (type_arg, *remaining_args)
                    break
                if isinstance(arg, StrawberryAuto):
                    remaining_args = [
                        a for a in args[1:] if not isinstance(a, StrawberryAuto)
                    ]
                    args = (args[0], arg, *remaining_args)
                    break

            # If we have only a StrawberryLazyReference and no more annotations,
            # we need to return the argument directly because Annotated
            # will raise an error if trying to instantiate it with only
            # one argument.
            if len(args) == 1:
                return args[0]

        # python 3.10 will return UnionType for origin, and it cannot be
        # subscripted like Union[Foo, Bar]
        if sys.version_info >= (3, 10):
            from types import UnionType

            if origin is UnionType:
                origin = Union

        # Future annotations in older versions will eval generic aliases to their
        # real types (i.e. List[foo] will have its origin set to list instead
        # of List). If that type is not subscriptable, retrieve its generic
        # alias version instead.
        if sys.version_info < (3, 9) and not hasattr(origin, "__class_getitem__"):
            origin = get_generic_alias(origin)

        type_ = (
            origin[tuple(eval_type(a, globalns, localns) for a in args)]
            if args
            else origin
        )

    return type_
