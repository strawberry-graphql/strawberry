"""Read the `Annotated` options of annotations that can't be evaluated yet.

Before Python 3.14, an annotation that uses names that aren't defined yet, like
a type defined further down the module, can't be evaluated when a type is
created. Its type can be resolved when the schema is built, but the options in
its `Annotated` metadata, like the permissions of a `strawberry.field()`, are
read when the type is created, so they would silently be ignored.
"""

from __future__ import annotations

import ast
import builtins
import dataclasses
from typing import TYPE_CHECKING, Annotated, Any, get_args, get_origin

from strawberry.exceptions import InvalidStrawberryFieldAnnotationError
from strawberry.types.field import StrawberryField

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Mapping


@dataclasses.dataclass(frozen=True)
class UnresolvedOptions:
    """Why the options of an annotation can't be read yet."""

    # the names used by the annotation that aren't defined yet
    undefined_names: list[str]
    # whether only the options use them, e.g. a permission class defined after
    # the type, while the type itself is defined
    in_options: bool


def is_strawberry_field(value: object) -> bool:
    return isinstance(value, StrawberryField)


def _lookup(node: ast.expr, namespace: Mapping[str, Any]) -> object:
    """Return the value of a name like `Annotated` or `strawberry.field`, if any."""
    if isinstance(node, ast.Name):
        return namespace.get(node.id, getattr(builtins, node.id, None))

    if isinstance(node, ast.Attribute):
        return getattr(_lookup(node.value, namespace), node.attr, None)

    return None


def _is_option(
    node: ast.expr,
    namespace: Mapping[str, Any],
    is_option: Callable[[object], bool],
) -> bool | None:
    """Return whether an item of `Annotated` metadata is an option.

    It's `None` when the item can't be evaluated yet, e.g. a helper that returns
    a `strawberry.field()` called with names that aren't defined yet.
    """
    try:
        # e.g. a helper that returns a `strawberry.field()`, or `relay.node()`
        value = eval(ast.unparse(node), dict(namespace))  # noqa: S307
    except Exception:  # noqa: BLE001
        return None

    return is_option(value)


def _is_options_alias(value: object, is_option: Callable[[object], bool]) -> bool:
    """Return whether `value` is an alias like `Annotated[T, strawberry.field()]`."""
    return get_origin(value) is Annotated and any(
        is_option(item) for item in get_args(value)[1:]
    )


def get_annotated_metadata(
    node: ast.expr, namespace: Mapping[str, Any]
) -> list[ast.expr] | None:
    """Return the metadata of `node` when it's an `Annotated[...]` subscript."""
    if (
        isinstance(node, ast.Subscript)
        and _lookup(node.value, namespace) is Annotated
        and isinstance(node.slice, ast.Tuple)
    ):
        return node.slice.elts[1:]

    return None


def _walk_options(node: ast.AST) -> Iterator[ast.AST]:
    """Walk the options in `Annotated` metadata, except types like `graphql_type`.

    Types are resolved when the schema is built, like the annotation itself.
    """
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.keyword) and child.arg == "graphql_type":
            continue

        yield child
        yield from _walk_options(child)


def _get_undefined_names(
    nodes: Iterable[ast.AST], namespace: Mapping[str, Any]
) -> set[str]:
    """Return the names used in `nodes` that aren't defined in `namespace`.

    Names bound in them, like the arguments of a lambda, count as defined.
    """
    used: set[str] = set()
    bound: set[str] = set()

    for node in nodes:
        if isinstance(node, ast.arg):
            bound.add(node.arg)
        elif isinstance(node, ast.Name):
            (used if isinstance(node.ctx, ast.Load) else bound).add(node.id)

    return {
        name
        for name in used - bound
        if name not in namespace and not hasattr(builtins, name)
    }


def get_undefined_option_names(
    metadata: Iterable[ast.expr], namespace: Mapping[str, Any]
) -> set[str]:
    """Return the names that options in `Annotated` metadata use but aren't defined."""
    return _get_undefined_names(
        (item for node in metadata for item in [node, *_walk_options(node)]),
        namespace,
    )


def find_unresolved_options(
    annotation: str,
    namespace: Mapping[str, Any],
    *,
    cls: type,
    field_name: str,
    is_option: Callable[[object], bool] = is_strawberry_field,
) -> UnresolvedOptions | None:
    """Return why the options of an annotation that can't be evaluated can't be read.

    The options are the items of its outermost `Annotated` that `is_option`
    accepts, like a `strawberry.field()`, including the ones of an alias like
    `AdminOnly[Account]`, and the items that can't be evaluated yet, as they could
    be options. It's `None` when it has none, as the type itself is resolved when
    the schema is built.

    A `strawberry.field()` is only allowed in the outermost `Annotated`, so one
    nested in the type, like in `list[Annotated[Account, strawberry.field()]]`,
    raises an `InvalidStrawberryFieldAnnotationError`.
    """
    try:
        expression = ast.parse(annotation, mode="eval").body
    except SyntaxError:
        return None

    # e.g. `Annotated[Account, strawberry.field(...)]`
    metadata = get_annotated_metadata(expression, namespace) or []

    def unresolved() -> UnresolvedOptions:
        options_names = get_undefined_option_names(metadata, namespace)
        undefined_names = _get_undefined_names(ast.walk(expression), namespace)

        # e.g. a quoted type, like `Annotated["Account", ...]`, but not strings in
        # the options, like `tags=["admin"]`
        type_node = (
            expression.slice.elts[0]
            if metadata
            and isinstance(expression, ast.Subscript)
            and isinstance(expression.slice, ast.Tuple)
            else expression
        )
        undefined_names |= {
            node.value
            for node in ast.walk(type_node)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value.isidentifier()
            and node.value not in namespace
            and not hasattr(builtins, node.value)
        }

        return UnresolvedOptions(
            undefined_names=sorted(undefined_names),
            in_options=bool(undefined_names) and undefined_names <= options_names,
        )

    if any(_is_option(item, namespace, is_option) is not False for item in metadata):
        return unresolved()

    # an alias with options, like `AdminOnly[Account]`, or `HiddenAccount` for
    # `Annotated[Account | None, ...]`, whose arguments aren't defined yet
    alias = expression.value if isinstance(expression, ast.Subscript) else expression

    if _is_options_alias(_lookup(alias, namespace), is_option):
        return unresolved()

    for node in ast.walk(expression):
        if node is expression or not isinstance(node, ast.Subscript):
            continue

        nested = [
            _is_option(item, namespace, is_strawberry_field)
            for item in get_annotated_metadata(node, namespace) or []
        ]

        if True in nested or _is_options_alias(
            _lookup(node.value, namespace), is_strawberry_field
        ):
            raise InvalidStrawberryFieldAnnotationError(field_name=field_name, cls=cls)

        if None in nested:
            return unresolved()

    return None


__all__ = [
    "UnresolvedOptions",
    "find_unresolved_options",
    "get_annotated_metadata",
    "get_undefined_option_names",
    "is_strawberry_field",
]
