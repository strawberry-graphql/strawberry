"""Field processing utilities for Pydantic models in Strawberry GraphQL.

This module provides functions to extract and process fields from Pydantic BaseModel
classes, converting them to StrawberryField instances that can be used in GraphQL schemas.
"""

from __future__ import annotations

import copy
import dataclasses
import datetime
import functools
import math
import operator
import sys
import uuid
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Annotated, Any, Optional, get_args, get_origin
from typing_extensions import Format, get_annotations

from pydantic import BaseModel

from strawberry.annotation import StrawberryAnnotation
from strawberry.exceptions import (
    InvalidStrawberryFieldAnnotationError,
    MultipleStrawberryFieldsError,
)
from strawberry.experimental.pydantic._compat import PydanticCompat
from strawberry.file_uploads import Upload
from strawberry.types.base import StrawberryObjectDefinition
from strawberry.types.field import StrawberryField, _contains_strawberry_field
from strawberry.types.maybe import _annotation_is_maybe
from strawberry.types.private import is_private
from strawberry.utils.typing import is_generic_alias, is_union

from .exceptions import (
    MaybeFieldError,
    StrawberryFieldAsDefaultError,
    UnregisteredTypeException,
    UploadFieldError,
)

if TYPE_CHECKING:
    from pydantic.fields import FieldInfo

    from strawberry.experimental.pydantic._compat import CompatModelField

from strawberry.experimental.pydantic._compat import is_new_type, lenient_issubclass


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


def _contains_upload(annotation: object) -> bool:
    return annotation is Upload or any(
        _contains_upload(arg) for arg in get_args(annotation)
    )


# GraphQL's Int is a 32-bit integer
_GRAPHQL_INT_RANGE = range(-(2**31), 2**31)
_CONSTANT_TYPES = (
    str,
    bool,
    Decimal,
    datetime.date,
    datetime.datetime,
    datetime.time,
    uuid.UUID,
)


def _is_constant_of_type(value: object, annotation: Any) -> bool:
    """Return whether `value` is a constant of the field type `annotation`.

    Values pydantic would have to convert first, like a string default for a
    date field, aren't constants of the field type.
    """
    if is_new_type(annotation):
        # e.g. `strawberry.ID` and scalars registered with `scalar_map`
        return _is_constant_of_type(value, annotation.__supertype__)

    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin is Annotated:
        return _is_constant_of_type(value, args[0])

    if is_union(annotation):
        types = [arg for arg in args if arg is not type(None)]

        return len(types) == 1 and _is_constant_of_type(value, types[0])

    if origin is list or (origin is tuple and args[1:] == (Ellipsis,)):
        return isinstance(value, (list, tuple)) and all(
            _is_constant_of_type(item, args[0]) for item in value
        )

    if lenient_issubclass(annotation, Enum):
        return isinstance(value, annotation)

    if annotation is int:
        return type(value) is int and value in _GRAPHQL_INT_RANGE

    if annotation is float:
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
        )

    return annotation in _CONSTANT_TYPES and type(value) is annotation


def _get_graphql_default(field_info: FieldInfo) -> object:
    """Return the default to publish in the GraphQL schema for an input field.

    graphql-core fills in published defaults before pydantic validates the
    input, so a field with a published default always ends up in
    `model_fields_set`. Only constants of the field's type are published, as
    they're part of the API. `None` defaults, default factories and other values
    are applied by pydantic, so that `model_dump(exclude_unset=True)` only
    contains what the client sent and factories run for every request.
    """
    if field_info.default_factory is not None or not _is_constant_of_type(
        field_info.default, field_info.annotation
    ):
        return dataclasses.MISSING

    return field_info.default


def _set_input_default(field: StrawberryField, field_info: FieldInfo) -> None:
    default = _get_graphql_default(field_info)

    # `StrawberryField.__copy__` builds `default_value` from `default`
    field.default = default
    field.default_factory = dataclasses.MISSING
    field.default_value = default

    # input fields can only be omitted when they're nullable or have a default,
    # so fields whose default is applied by pydantic become nullable
    if default is dataclasses.MISSING and not field_info.is_required():
        assert field.type_annotation is not None

        field.type_annotation = StrawberryAnnotation(
            Optional[field.type_annotation.raw_annotation],  # noqa: UP045
            namespace=field.type_annotation.namespace,
        )


def replace_pydantic_types(type_: Any, is_input: bool, model: type[BaseModel]) -> Any:
    """Replace Pydantic types with their Strawberry equivalents for first-class integration."""
    from pydantic import BaseModel

    if lenient_issubclass(type_, BaseModel):
        # `model` can reference itself, but it's only registered after its fields
        if type_ is model or hasattr(type_, "__strawberry_definition__"):
            return type_

        raise UnregisteredTypeException(type_)

    return type_


def replace_types_recursively(
    type_: Any,
    is_input: bool,
    compat: PydanticCompat,
    model: type[BaseModel],
) -> Any:
    """Recursively replace Pydantic types with their Strawberry equivalents."""
    # NewTypes are resolved by the schema's scalar registry, like with
    # `@strawberry.type`: that's how `strawberry.ID`, `JSON`, `Upload` and
    # `scalar_map` scalars work, so they must not be replaced by their supertype
    basic_type = type_ if is_new_type(type_) else compat.get_basic_type(type_)
    replaced_type = replace_pydantic_types(basic_type, is_input, model)

    origin = get_origin(type_)

    if not origin or not hasattr(type_, "__args__"):
        return replaced_type

    converted = tuple(
        replace_types_recursively(t, is_input=is_input, compat=compat, model=model)
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
    field: CompatModelField,
    is_input: bool,
    compat: PydanticCompat,
    model: type[BaseModel],
) -> Any:
    """Get the GraphQL type for a field of `model`."""
    return replace_types_recursively(
        field.outer_type_, is_input, compat=compat, model=model
    )


def _create_strawberry_field(
    cls: type[BaseModel],
    origin: type,
    field_name: str,
    pydantic_field: CompatModelField,
    field_info: FieldInfo | None,
    *,
    is_input: bool,
    compat: PydanticCompat,
) -> StrawberryField:
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
            get_type_for_field(pydantic_field, is_input, compat=compat, model=cls),
            namespace=vars(module) if module is not None else None,
        )
    elif strawberry_field.type_annotation.namespace is None:
        # set by `strawberry.field(graphql_type=...)`
        strawberry_field.type_annotation.set_namespace_from_field(strawberry_field)

    # pydantic applies defaults when it builds the model
    strawberry_field.default = dataclasses.MISSING
    strawberry_field.default_factory = dataclasses.MISSING
    strawberry_field.default_value = dataclasses.MISSING

    return strawberry_field


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
    field_infos: dict[str, FieldInfo] = cls.model_fields
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

            # Uploads are the integration's file objects, which pydantic would
            # reject on every request when validating them as `Upload` (bytes)
            if is_input and _contains_upload(field_info.annotation):
                raise UploadFieldError(field_name=field_name, cls=origin)

            if is_input and _annotation_is_maybe(field_info.annotation):
                raise MaybeFieldError(field_name=field_name, cls=origin)

        if (base_field := _get_strawberry_base_field(origin, field_name)) is not None:
            # inputs replace the field's default with pydantic's below
            strawberry_field = copy.copy(base_field) if is_input else base_field
        else:
            strawberry_field = _create_strawberry_field(
                cls,
                origin,
                field_name,
                pydantic_field,
                field_info,
                is_input=is_input,
                compat=compat,
            )

        if is_input and field_info is not None:
            _set_input_default(strawberry_field, field_info)

        fields.append(strawberry_field)

    return fields


__all__ = [
    "_get_pydantic_fields",
    "replace_pydantic_types",
    "replace_types_recursively",
]
