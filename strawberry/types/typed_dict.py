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
from typing import (
    TYPE_CHECKING,
    Any,
)
from typing_extensions import (
    NotRequired,
    Required,
    get_type_hints,
    is_typeddict,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

from strawberry.annotation import StrawberryAnnotation
from strawberry.types.base import StrawberryObjectDefinition, has_object_definition
from strawberry.types.field import StrawberryField
from strawberry.types.fields.resolver import StrawberryResolver
from strawberry.types.unset import UNSET

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
        TypedDictValidationError: If required keys are missing, the type is invalid
        or the TypedDict is undecorated.
    """
    if not isinstance(data, dict):
        raise TypedDictValidationError(
            f"Expected a dictionary, got {type(data).__name__}"
        )

    definition = getattr(typed_dict_cls, "__strawberry_definition__", None)
    if not definition:
        raise TypedDictValidationError(
            f"{typed_dict_cls.__name__} is not a Strawberry TypedDict"
        )

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
    strawberry_field: StrawberryField | None


def _normalize_typed_dict_annotation(
    annotation: Any,
    *,
    required_by_default: bool,
) -> NormalizedTypedDictAnnotation:
    required = required_by_default
    description = None
    strawberry_field: StrawberryField | None = None

    while True:
        origin = typing.get_origin(annotation)

        if origin is typing.Annotated:
            args = typing.get_args(annotation)

            annotation = args[0]

            for meta in args[1:]:
                if isinstance(meta, str):
                    description = meta

                elif isinstance(meta, StrawberryField):
                    strawberry_field = meta

                    if meta.description:
                        description = meta.description

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
        strawberry_field=strawberry_field,
    )


def _is_optional(annotation: Any) -> bool:
    origin = typing.get_origin(annotation)

    if origin in (typing.Union, types.UnionType):
        return type(None) in typing.get_args(annotation)

    return False


def _synthesize_nested_typed_dicts(
    annotation: Any,
    *,
    is_input: bool,
) -> None:
    origin = typing.get_origin(annotation)

    if is_typeddict(annotation):
        if not has_object_definition(annotation):
            definition = create_typed_dict_definition(
                annotation,
                name=None,
                description=None,
                directives=(),
                is_input=is_input,
            )

            annotation.__strawberry_definition__ = definition

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


def create_typed_dict_definition(
    typed_dict_cls: type[Any],
    name: str | None,
    description: str | None,
    directives: Sequence[object] | None = (),
    *,
    is_input: bool,
) -> StrawberryObjectDefinition:
    """Dynamically generates a StrawberryObjectDefinition from a TypedDict class."""
    existing = getattr(
        typed_dict_cls,
        "__strawberry_definition__",
        None,
    )

    if existing is not None:
        return existing

    required_keys: frozenset[str] = getattr(
        typed_dict_cls,
        "__required_keys__",
        frozenset(),
    )

    def default_is_type_of(obj: Any, _info: Any) -> bool:
        return isinstance(obj, dict) and required_keys.issubset(obj)

    definition = StrawberryObjectDefinition(
        name=name or typed_dict_cls.__name__,
        is_input=is_input,
        is_interface=False,
        origin=typed_dict_cls,
        description=description,
        interfaces=[],
        extend=False,
        directives=directives or (),
        is_type_of=default_is_type_of,
        resolve_type=None,
        fields=[],
    )

    total = getattr(typed_dict_cls, "__total__", True)
    module = sys.modules.get(typed_dict_cls.__module__)
    namespace = module.__dict__ if module else {}

    # Extract hints preserving wrappers (Required / NotRequired)
    try:
        hints_with_extras = get_type_hints(
            typed_dict_cls,
            globalns=namespace,
            include_extras=True,
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
            graphql_type = graphql_type | None

        resolver = _make_key_resolver(field_name, is_req)

        type_annotation = StrawberryAnnotation(
            annotation=graphql_type,
            namespace=namespace,
        )

        extra_field = normalized.strawberry_field

        field = StrawberryField(
            python_name=field_name,
            graphql_name=(
                normalized.strawberry_field.graphql_name
                if normalized.strawberry_field
                else None
            ),
            type_annotation=type_annotation,
            origin=typed_dict_cls,
            description=normalized.description,
            directives=(extra_field.directives if extra_field else ()),
            permission_classes=(extra_field.permission_classes if extra_field else []),
            deprecation_reason=(
                extra_field.deprecation_reason if extra_field else None
            ),
            extensions=(extra_field.extensions if extra_field else []),
            default=dataclasses.MISSING,
            metadata={
                "typed_dict_required": is_req,
            },
        )

        field.base_resolver = resolver
        field.default_value = UNSET

        fields.append(field)

    definition.fields = fields

    typed_dict_cls.__strawberry_definition__ = definition

    return definition


__all__ = [
    "TypedDictValidationError",
    "create_typed_dict_definition",
    "validate_typed_dict",
]
