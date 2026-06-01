"""Native support for TypedDict in Strawberry GraphQL.

This module provides decorators to natively convert Python's `typing.TypedDict`
into Strawberry GraphQL output and input types. It features robust support for
Python's nuanced nullability rules, metadata extraction via `typing.Annotated`,
and runtime validation utilities.
"""

from __future__ import annotations

import dataclasses
import sys
import types
import typing
import warnings
from typing import (
    TYPE_CHECKING,
    Any,
    Optional,
    overload,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence

from strawberry.annotation import StrawberryAnnotation
from strawberry.types.base import StrawberryObjectDefinition, has_object_definition
from strawberry.types.field import StrawberryField
from strawberry.types.fields.resolver import StrawberryResolver
from strawberry.types.unset import UNSET

try:
    from typing_extensions import is_typeddict
except ImportError:  # pragma: no cover

    def is_typeddict(tp: type[Any]) -> bool:
        """Fallback check for TypedDict across standard library and extensions."""
        return (
            isinstance(tp, type)
            and hasattr(tp, "__total__")
            and hasattr(tp, "__required_keys__")
            and hasattr(tp, "__optional_keys__")
        )


_REQUIRED_TYPES: tuple[object, ...] = ()
_NOT_REQUIRED_TYPES: tuple[object, ...] = ()

if sys.version_info >= (3, 11):
    from typing import NotRequired, Required

    _REQUIRED_TYPES += (Required,)
    _NOT_REQUIRED_TYPES += (NotRequired,)

try:
    from typing_extensions import NotRequired as _ExtNotRequired
    from typing_extensions import Required as _ExtRequired

    _REQUIRED_TYPES += (_ExtRequired,)
    _NOT_REQUIRED_TYPES += (_ExtNotRequired,)
except ImportError:
    pass


class TypedDictRegistry:
    """Caches generated Strawberry definitions for TypedDict classes."""

    def __init__(self) -> None:
        self._definitions_by_key: dict[
            tuple[type[Any], bool, str | None],
            StrawberryObjectDefinition,
        ] = {}

    def get(
        self,
        cls: type[Any],
        *,
        is_input: bool,
        name: str | None,
    ) -> StrawberryObjectDefinition | None:
        return self._definitions_by_key.get((cls, is_input, name))

    def set(
        self,
        cls: type[Any],
        *,
        is_input: bool,
        name: str | None,
        definition: StrawberryObjectDefinition,
    ) -> None:
        self._definitions_by_key[(cls, is_input, name)] = definition


_typed_dict_registry = TypedDictRegistry()


class TypedDictValidationError(Exception):
    """Exception raised when a dictionary fails runtime TypedDict validation."""


def validate_typed_dict(
    data: dict[str, Any],
    typed_dict_cls: type[Any],
) -> None:
    """Validates at runtime that a dictionary conforms to its TypedDict definition.

    Ensures no required keys are missing. This is useful because Strawberry
    normally defers key lookups until execution, which could result in a KeyError.

    Args:
        data (dict): The dictionary returned by the resolver.
        typed_dict_cls (Type[Any]): The TypedDict class it claims to represent.

    Raises:
        TypedDictValidationError: If required keys are missing or the type is invalid.
    """
    if not isinstance(data, dict):
        raise TypedDictValidationError(
            f"Expected a dictionary, got {type(data).__name__}"
        )

    definition = getattr(typed_dict_cls, "__strawberry_definition__", None)
    if not definition:
        return

    # Extract required keys from Strawberry definitions
    required_keys = {
        f.python_name
        for f in definition.fields
        if f.metadata.get("typed_dict_required", False)
    }

    missing_keys = required_keys - data.keys()
    if missing_keys:
        raise TypedDictValidationError(
            f"Missing required keys for {typed_dict_cls.__name__}: {', '.join(sorted(missing_keys))}"
        )


@dataclasses.dataclass(frozen=True)
class NormalizedTypedDictAnnotation:
    annotation: Any
    required: bool
    description: str | None
    directives: list[Any]


def _is_optional(annotation: Any) -> bool:
    origin = typing.get_origin(annotation)

    if origin in (typing.Union, types.UnionType):
        return type(None) in typing.get_args(annotation)

    return False


def _normalize_typed_dict_annotation(
    annotation: Any,
    *,
    required_by_default: bool,
) -> NormalizedTypedDictAnnotation:
    required = required_by_default
    description = None
    directives: list[Any] = []

    while True:
        origin = typing.get_origin(annotation)

        if origin is typing.Annotated:
            args = typing.get_args(annotation)

            annotation = args[0]

            for meta in args[1:]:
                if isinstance(meta, str):
                    description = meta

                elif isinstance(meta, StrawberryField):
                    if meta.description:
                        description = meta.description

                    if meta.directives:
                        directives.extend(meta.directives)

            continue

        if origin in _REQUIRED_TYPES:
            required = True
            annotation = typing.get_args(annotation)[0]
            continue

        if origin in _NOT_REQUIRED_TYPES:
            required = False
            annotation = typing.get_args(annotation)[0]
            continue

        break

    return NormalizedTypedDictAnnotation(
        annotation=annotation,
        required=required,
        description=description,
        directives=directives,
    )


def _synthesize_nested_typed_dicts(
    annotation: Any,
    *,
    is_input: bool,
) -> None:
    origin = typing.get_origin(annotation)

    if is_typeddict(annotation):
        if not has_object_definition(annotation):
            _apply_typed_dict(
                annotation,
                name=None,
                description=None,
                directives=(),
                is_input=is_input,
            )
        return

    if origin is None:
        return

    for arg in typing.get_args(annotation):
        if arg is type(None):
            continue

        _synthesize_nested_typed_dicts(
            arg,
            is_input=is_input,
        )


def _make_key_resolver(key: str, required: bool) -> StrawberryResolver:
    """Generates a dynamic field resolver for a TypedDict key.

    Unlike standard classes which use `getattr(obj, key)`, TypedDicts
    are resolved at runtime using dictionary subscripting `obj[key]`.
    """
    if required:

        def resolver(self: Any) -> Any:
            return self[key]
    else:

        def resolver(self: Any) -> Any:
            return self.get(key, None)

    return StrawberryResolver(resolver)


def _create_typed_dict_definition(
    typed_dict_cls: type[Any],
    name: str | None,
    description: str | None,
    directives: Sequence[object],
    is_input: bool,
) -> StrawberryObjectDefinition:
    """Dynamically generates a StrawberryObjectDefinition from a TypedDict class."""
    existing = _typed_dict_registry.get(
        typed_dict_cls,
        is_input=is_input,
        name=name,
    )

    if existing is not None:
        return existing

    definition = StrawberryObjectDefinition(
        name=name or typed_dict_cls.__name__,
        is_input=is_input,
        is_interface=False,
        origin=typed_dict_cls,
        description=description,
        interfaces=[],
        extend=False,
        directives=directives,
        is_type_of=None,
        resolve_type=None,
        fields=[],
    )
    _typed_dict_registry.set(
        typed_dict_cls,
        is_input=is_input,
        name=name,
        definition=definition,
    )

    total = getattr(typed_dict_cls, "__total__", True)
    module = sys.modules.get(typed_dict_cls.__module__)
    namespace = module.__dict__ if module else {}

    # Extract hints preserving wrappers (Required / NotRequired)
    try:
        try:
            from typing_extensions import get_type_hints as get_type_hints_ext
        except ImportError:
            from typing import get_type_hints as get_type_hints_ext

        hints_with_extras = get_type_hints_ext(
            typed_dict_cls, globalns=namespace, include_extras=True
        )
    except (TypeError, NameError):
        hints_with_extras = getattr(typed_dict_cls, "__annotations__", {})

    fields: list[StrawberryField] = []

    for field_name, raw_hint in hints_with_extras.items():
        if field_name.startswith("_"):
            continue

        normalized = _normalize_typed_dict_annotation(
            raw_hint,
            required_by_default=total,
        )

        base_type = normalized.annotation
        is_req = normalized.required

        _synthesize_nested_typed_dicts(
            base_type,
            is_input=is_input,
        )

        graphql_type = base_type

        if not is_req and not _is_optional(graphql_type):
            graphql_type = Optional[graphql_type]  # noqa: UP045

        resolver = _make_key_resolver(field_name, is_req)

        type_annotation = StrawberryAnnotation(
            annotation=graphql_type,
            namespace=namespace,
        )

        field = StrawberryField(
            python_name=field_name,
            graphql_name=None,
            type_annotation=type_annotation,
            origin=typed_dict_cls,
            description=normalized.description,
            directives=normalized.directives,
            default=dataclasses.MISSING,
            metadata={
                "typed_dict_required": is_req,
            },
        )

        field.base_resolver = resolver
        field.default_value = UNSET

        fields.append(field)

    definition.fields = fields
    return definition


def _apply_typed_dict(
    cls: type[Any] | None,
    name: str | None,
    description: str | None,
    directives: Sequence[object],
    is_input: bool,
) -> Any:
    if cls is None:
        return lambda cls_: _apply_typed_dict(
            cls_, name, description, directives, is_input
        )

    if not is_typeddict(cls):
        raise TypeError(
            f"@strawberry.typed_dict can only be applied to TypedDict classes, got {cls!r}"
        )

    existing = _typed_dict_registry.get(
        cls,
        is_input=is_input,
        name=name,
    )

    if existing is not None:
        warnings.warn(
            f"TypedDict {cls.__name__} is already registered",
            stacklevel=2,
        )
        return cls

    definition = _create_typed_dict_definition(
        cls, name, description, directives, is_input
    )
    cls.__strawberry_definition__ = definition
    return cls


@overload
def typed_dict(
    cls: type[Any],
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Iterable[object] = (),
) -> type[Any]: ...


@overload
def typed_dict(
    cls: None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Iterable[object] = (),
) -> Callable[[type[Any]], type[Any]]: ...


def typed_dict(
    cls: type[Any] | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Iterable[object] = (),
) -> Any:
    """Annotates a TypedDict as a Strawberry GraphQL output type.

    Args:
        cls: The TypedDict class to annotate.
        name: The GraphQL name of the type.
        description: The GraphQL description of the type.
        directives: The directives to attach to the type.

    Returns:
        The decorated TypedDict class.

    Example:

    ```python
    from typing import TypedDict
    import strawberry


    @strawberry.typed_dict
    class User(TypedDict):
        id: int
        name: str
    ```

    The above code will generate the following GraphQL schema:

    ```graphql
    type User {
        id: Int!
        name: String!
    }
    ```
    """
    return _apply_typed_dict(
        cls,
        name,
        description,
        tuple(directives),
        is_input=False,
    )


@overload
def typed_dict_input(
    cls: type[Any],
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Iterable[object] = (),
) -> type[Any]: ...


@overload
def typed_dict_input(
    cls: None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Iterable[object] = (),
) -> Callable[[type[Any]], type[Any]]: ...


def typed_dict_input(
    cls: type[Any] | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Iterable[object] = (),
) -> Any:
    """Annotates a TypedDict as a Strawberry GraphQL input type.

    Args:
        cls: The TypedDict class to annotate.
        name: The GraphQL name of the input type.
        description: The GraphQL description of the input type.
        directives: The directives to attach to the input type.

    Returns:
        The decorated TypedDict class.

    Example:

    ```python
    from typing import TypedDict
    import strawberry


    @strawberry.typed_dict_input
    class CreateUserInput(TypedDict):
        name: str
        age: int
    ```
    """
    return _apply_typed_dict(
        cls,
        name,
        description,
        tuple(directives),
        is_input=True,
    )


__all__ = [
    "TypedDictValidationError",
    "typed_dict",
    "typed_dict_input",
    "validate_typed_dict",
]
