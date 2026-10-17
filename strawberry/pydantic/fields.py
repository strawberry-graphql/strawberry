"""Read the fields of Pydantic models as Strawberry fields."""

from __future__ import annotations

import copy
import dataclasses
import datetime as dt
import math
import sys
import uuid
from collections import abc
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Annotated, Any, Optional, get_args, get_origin
from typing_extensions import Format, get_annotations

from graphql.type.directives import DEFAULT_DEPRECATION_REASON
from pydantic import BaseModel

from strawberry.annotation import StrawberryAnnotation
from strawberry.file_uploads import Upload
from strawberry.types.base import StrawberryObjectDefinition
from strawberry.types.field import StrawberryField, get_annotated_field
from strawberry.types.maybe import _annotation_is_maybe
from strawberry.types.private import is_private
from strawberry.utils.typing import is_union

from .exceptions import (
    InheritedDefaultFactoryError,
    MaybeFieldError,
    StrawberryFieldAsDefaultError,
    UnregisteredPydanticTypeError,
    UploadFieldError,
)

if TYPE_CHECKING:
    from pydantic.fields import FieldInfo


def _is_new_type(annotation: object) -> bool:
    return callable(annotation) and hasattr(annotation, "__supertype__")


def _is_subclass(annotation: object, base: type | tuple[type, ...]) -> bool:
    return isinstance(annotation, type) and issubclass(annotation, base)


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

    return definition.get_field(field_name)


def _get_strawberry_field_override(
    field_info: FieldInfo, cls: type, field_name: str
) -> StrawberryField | None:
    """Return the `strawberry.field()` from `Annotated[T, strawberry.field()]`.

    `cls` is the class that declares the field.
    """
    # Pydantic treats a `strawberry.field()` assigned as the default like a
    # dataclass field: it keeps its default and discards everything else. The
    # original object is only kept on a private attribute, so this check is best
    # effort.
    if isinstance(getattr(field_info, "_original_assignment", None), StrawberryField):
        raise StrawberryFieldAsDefaultError(field_name=field_name, cls=cls)

    # pydantic keeps the metadata of the field's `Annotated` apart from its type
    annotation = (
        Annotated[(field_info.annotation, *field_info.metadata)]
        if field_info.metadata
        else field_info.annotation
    )
    _, strawberry_field = get_annotated_field(
        annotation, cls=cls, field_name=field_name
    )

    return strawberry_field


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
    dt.date,
    dt.datetime,
    dt.time,
    uuid.UUID,
)


def _is_constant_of_type(value: object, annotation: Any) -> bool:
    """Return whether `value` is a constant of the field type `annotation`.

    Values pydantic would have to convert first, like a string default for a
    date field, aren't constants of the field type.
    """
    if _is_new_type(annotation):
        # e.g. `strawberry.ID` and scalars registered with `scalar_map`
        return _is_constant_of_type(value, annotation.__supertype__)

    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin is Annotated:
        return _is_constant_of_type(value, args[0])

    if is_union(annotation):
        types = [arg for arg in args if arg is not type(None)]

        return len(types) == 1 and _is_constant_of_type(value, types[0])

    # bare `typing.List` and `typing.Sequence` don't have an item type
    if args and (
        origin in (list, abc.Sequence) or (origin is tuple and args[1:] == (Ellipsis,))
    ):
        # GraphQL passes lists, which pydantic keeps as they are for sequences, so
        # a tuple default of a sequence would reach resolvers as a list
        containers = list if origin is abc.Sequence else (list, tuple)

        return isinstance(value, containers) and all(
            _is_constant_of_type(item, args[0]) for item in value
        )

    if _is_subclass(annotation, Enum):
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


def _find_unregistered_model(
    type_: Any, model: type[BaseModel]
) -> type[BaseModel] | None:
    """Return a model used in `type_` that doesn't have a GraphQL type, if any."""
    if _is_subclass(type_, BaseModel):
        # `model` can reference itself, but it's only registered after its
        # fields. The definition is inherited by subclasses, which would
        # otherwise be the GraphQL type of their decorated base, and by
        # parametrized generic models, like `Page[User]`
        if type_ is model or "__strawberry_definition__" in vars(type_):
            return None

        return type_

    return next(
        (
            unregistered
            for arg in get_args(type_)
            if (unregistered := _find_unregistered_model(arg, model)) is not None
        ),
        None,
    )


def _create_strawberry_field(
    cls: type[BaseModel],
    origin: type,
    field_name: str,
    field_info: FieldInfo,
    *,
    is_input: bool,
) -> StrawberryField:
    annotation = field_info.annotation
    description = field_info.description
    strawberry_override = _get_strawberry_field_override(field_info, origin, field_name)

    # Start from the user's `strawberry.field()`, so all of its options are
    # kept, and fill in what pydantic knows about the field
    strawberry_field = (
        copy.copy(strawberry_override)
        if strawberry_override is not None
        else StrawberryField()
    )
    # pydantic aliases describe the model's own (de)serialization, so like with
    # `@strawberry.type` the GraphQL name comes from the python name, unless set
    # with `strawberry.field(name=...)`
    strawberry_field.python_name = field_name
    strawberry_field.origin = cls

    if strawberry_field.description is None:
        strawberry_field.description = description

    # like `strawberry.field(deprecation_reason=...)`, deprecating a required
    # input field fails schema validation, as GraphQL doesn't allow it
    if strawberry_field.deprecation_reason is None and field_info.deprecated:
        strawberry_field.deprecation_reason = (
            DEFAULT_DEPRECATION_REASON
            if field_info.deprecated is True
            else field_info.deprecation_message
        )

    # types are resolved in the module declaring the field
    module = sys.modules.get(origin.__module__)
    namespace = vars(module) if module is not None else None

    if strawberry_field.type_annotation is None:
        if (unregistered := _find_unregistered_model(annotation, cls)) is not None:
            raise UnregisteredPydanticTypeError(
                unregistered, cls=origin, field_name=field_name, is_input=is_input
            )

        strawberry_field.type_annotation = StrawberryAnnotation(
            annotation, namespace=namespace
        )
    else:
        # set by `strawberry.field(graphql_type=...)`, whose annotation can be
        # shared with other types, e.g. through a type alias, so each field gets
        # its own, instead of setting the namespace of the shared one
        strawberry_field.type_annotation = StrawberryAnnotation(
            strawberry_field.type_annotation.raw_annotation, namespace=namespace
        )

    # pydantic applies defaults when it builds the model
    strawberry_field.default = dataclasses.MISSING
    strawberry_field.default_factory = dataclasses.MISSING
    strawberry_field.default_value = dataclasses.MISSING

    return strawberry_field


def get_pydantic_fields(
    cls: type[BaseModel], is_input: bool = False
) -> list[StrawberryField]:
    """Return the Strawberry fields of a Pydantic model.

    Pydantic is the source of truth for which fields exist: its `model_fields`
    already resolved string annotations and merged inherited fields. Fields are
    excluded from the schema when they are marked with `strawberry.Private` or,
    for output types, with pydantic's `Field(exclude=True)`.

    Fields can be customized using `Annotated`, like with `@strawberry.type`:

    @strawberry.pydantic.type
    class User(BaseModel):
        name: str
        age: Annotated[int, strawberry.field(directives=[SomeDirective()])]
    """
    fields: list[StrawberryField] = []

    origins = _get_field_origins(cls)

    for field_name, field_info in cls.model_fields.items():
        origin = origins.get(field_name, cls)

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
            # dataclasses don't keep a default factory on the class, so pydantic
            # doesn't see it and requires the field, which clients can omit when
            # it's nullable
            if (
                is_input
                and field_info.is_required()
                and base_field.default_factory is not dataclasses.MISSING
            ):
                raise InheritedDefaultFactoryError(
                    field_name=field_name, cls=cls, base=origin
                )

            # inputs replace the field's default with pydantic's below
            strawberry_field = copy.copy(base_field) if is_input else base_field
        else:
            strawberry_field = _create_strawberry_field(
                cls, origin, field_name, field_info, is_input=is_input
            )

        if is_input:
            _set_input_default(strawberry_field, field_info)

        fields.append(strawberry_field)

    return fields


__all__ = ["get_pydantic_fields"]
