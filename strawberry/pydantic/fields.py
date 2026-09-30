"""Field processing utilities for Pydantic models in Strawberry GraphQL.

This module provides functions to extract and process fields from Pydantic BaseModel
classes, converting them to StrawberryField instances that can be used in GraphQL schemas.
"""

from __future__ import annotations

import copy
import dataclasses
import functools
import operator
import sys
from typing import TYPE_CHECKING, Any, get_args, get_origin
from typing_extensions import Format, get_annotations

from pydantic import BaseModel

from strawberry.annotation import StrawberryAnnotation
from strawberry.exceptions import (
    InvalidStrawberryFieldAnnotationError,
    MultipleStrawberryFieldsError,
)
from strawberry.experimental.pydantic._compat import PydanticCompat
from strawberry.experimental.pydantic.utils import get_default_factory_for_field
from strawberry.types.base import StrawberryObjectDefinition
from strawberry.types.field import StrawberryField, _contains_strawberry_field
from strawberry.types.private import is_private
from strawberry.utils.typing import is_generic_alias, is_union

from .exceptions import StrawberryFieldAsDefaultError, UnregisteredTypeException

if TYPE_CHECKING:
    from pydantic.fields import FieldInfo

    from strawberry.experimental.pydantic._compat import CompatModelField

from strawberry.experimental.pydantic._compat import lenient_issubclass


def _get_field_origins(cls: type[BaseModel]) -> dict[str, type]:
    """Map each annotated name to the class in the MRO that declares it."""
    origins: dict[str, type] = {}

    for base in cls.__mro__:
        for name in get_annotations(base, format=Format.FORWARDREF):
            origins.setdefault(name, base)

    return origins


def _get_strawberry_base_field(origin: type, field_name: str) -> StrawberryField | None:
    """Return the field declared on a regular Strawberry type or interface.

    Pydantic collects fields declared on non-pydantic bases too, but it doesn't
    know about their `strawberry.field()` configuration (e.g. permissions), so we
    reuse the Strawberry field, like `@strawberry.type` does for its bases.
    """
    if issubclass(origin, BaseModel):
        return None

    # only the class's own definition, not one inherited from its bases
    definition = vars(origin).get("__strawberry_definition__")

    if not isinstance(definition, StrawberryObjectDefinition):
        return None

    return next(
        (field for field in definition.fields if field.python_name == field_name),
        None,
    )


def _get_strawberry_field_override(
    field_info: FieldInfo, cls: type, field_name: str
) -> StrawberryField | None:
    """Return the `strawberry.field()` from `Annotated[T, strawberry.field()]`."""
    # Pydantic treats a `strawberry.field()` assigned as the default like a
    # dataclass field: it keeps its default and discards everything else. The
    # original object is only kept on a private attribute, so this check is best
    # effort.
    if isinstance(getattr(field_info, "_original_assignment", None), StrawberryField):
        raise StrawberryFieldAsDefaultError(field_name=field_name, cls=cls)

    if _contains_strawberry_field(field_info.annotation):
        raise InvalidStrawberryFieldAnnotationError(field_name=field_name, cls=cls)

    strawberry_fields = [
        item for item in field_info.metadata if isinstance(item, StrawberryField)
    ]

    if len(strawberry_fields) > 1:
        raise MultipleStrawberryFieldsError(field_name=field_name, cls=cls)

    return strawberry_fields[0] if strawberry_fields else None


def replace_pydantic_types(type_: Any, is_input: bool) -> Any:
    """Replace Pydantic types with their Strawberry equivalents for first-class integration."""
    from pydantic import BaseModel

    if lenient_issubclass(type_, BaseModel):
        if hasattr(type_, "__strawberry_definition__"):
            return type_

        raise UnregisteredTypeException(type_)

    return type_


def replace_types_recursively(
    type_: Any,
    is_input: bool,
    compat: PydanticCompat,
) -> Any:
    """Recursively replace Pydantic types with their Strawberry equivalents."""
    # For now, use a simpler approach similar to the experimental module
    basic_type = compat.get_basic_type(type_)
    replaced_type = replace_pydantic_types(basic_type, is_input)

    origin = get_origin(type_)

    if not origin or not hasattr(type_, "__args__"):
        return replaced_type

    converted = tuple(
        replace_types_recursively(t, is_input=is_input, compat=compat)
        for t in get_args(replaced_type)
    )

    # Handle special cases for typing generics
    if is_generic_alias(replaced_type):
        # Use origin[converted] to reconstruct the generic type
        return origin[converted]
    if is_union(replaced_type):
        # Use functools.reduce with operator.or_ to create X | Y | Z union type
        return functools.reduce(operator.or_, converted)

    # Fallback to origin[converted] for standard generic types
    return origin[converted]


def get_type_for_field(
    field: CompatModelField, is_input: bool, compat: PydanticCompat
) -> Any:
    """Get the GraphQL type for a Pydantic field."""
    return replace_types_recursively(field.outer_type_, is_input, compat=compat)


def _get_pydantic_fields(
    cls: type[BaseModel],
    is_input: bool = False,
    include_computed: bool = False,
) -> list[StrawberryField]:
    """Extract StrawberryFields from a Pydantic BaseModel class.

    Pydantic is the source of truth for which fields exist: its `model_fields`
    already resolved string annotations and merged inherited fields. Fields are
    excluded from the schema when they are marked with `strawberry.Private` or,
    for output types, with pydantic's `Field(exclude=True)`.

    Fields can be customized using `Annotated`, like with `@strawberry.type`:

    @strawberry.pydantic.type
    class User(BaseModel):
        name: str
        age: Annotated[int, strawberry.field(directives=[SomeDirective()])]

    Args:
        cls: The Pydantic BaseModel class to extract fields from
        is_input: Whether this is for an input type
        include_computed: Whether to include computed fields

    Returns:
        List of StrawberryField instances
    """
    fields: list[StrawberryField] = []

    compat = PydanticCompat.from_model(cls)
    model_fields = compat.get_model_fields(cls, include_computed=include_computed)
    field_infos: dict[str, FieldInfo] = getattr(cls, "model_fields", {})
    origins = _get_field_origins(cls)

    for field_name, pydantic_field in model_fields.items():
        origin = origins.get(field_name, cls)
        # computed fields don't have a FieldInfo
        field_info = field_infos.get(field_name)

        if field_info is not None:
            if is_private(field_info.rebuild_annotation()):
                continue

            # `exclude=True` hides a field from pydantic's serialization, so we
            # hide it from the GraphQL output too
            if field_info.exclude is True and not is_input:
                continue

        if (base_field := _get_strawberry_base_field(origin, field_name)) is not None:
            fields.append(base_field)
            continue

        strawberry_override = (
            _get_strawberry_field_override(field_info, origin, field_name)
            if field_info is not None
            else None
        )

        # Start from the user's `strawberry.field()`, so all of its options are
        # kept, and fill in what pydantic knows about the field
        strawberry_field = (
            copy.copy(strawberry_override)
            if strawberry_override is not None
            else StrawberryField()
        )
        strawberry_field.python_name = field_name
        strawberry_field.origin = cls

        if strawberry_field.graphql_name is None:
            strawberry_field.graphql_name = pydantic_field.alias

        if strawberry_field.description is None:
            strawberry_field.description = pydantic_field.description

        if strawberry_field.type_annotation is None:
            module = sys.modules.get(origin.__module__)

            strawberry_field.type_annotation = StrawberryAnnotation(
                get_type_for_field(pydantic_field, is_input, compat=compat),
                namespace=vars(module) if module is not None else None,
            )
        elif strawberry_field.type_annotation.namespace is None:
            # set by `strawberry.field(graphql_type=...)`
            strawberry_field.type_annotation.set_namespace_from_field(strawberry_field)

        default_factory = get_default_factory_for_field(pydantic_field, compat=compat)
        strawberry_field.default = dataclasses.MISSING
        strawberry_field.default_factory = default_factory
        strawberry_field.default_value = (
            default_factory() if callable(default_factory) else dataclasses.MISSING
        )

        fields.append(strawberry_field)

    return fields


__all__ = [
    "_get_pydantic_fields",
    "replace_pydantic_types",
    "replace_types_recursively",
]
