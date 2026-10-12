"""Field processing utilities for Pydantic models in Strawberry GraphQL.

This module provides functions to extract and process fields from Pydantic BaseModel
classes, converting them to StrawberryField instances that can be used in GraphQL schemas.
"""

from __future__ import annotations

import copy
import dataclasses
import sys
from typing import TYPE_CHECKING, Any, Union, get_args, get_origin
from typing_extensions import Format, get_annotations

from graphql.type.directives import DEFAULT_DEPRECATION_REASON
from pydantic import BaseModel

from strawberry.annotation import StrawberryAnnotation
from strawberry.exceptions import (
    InvalidStrawberryFieldAnnotationError,
    MultipleStrawberryFieldsError,
)
from strawberry.types.base import StrawberryObjectDefinition
from strawberry.types.field import StrawberryField, _contains_strawberry_field
from strawberry.types.private import is_private
from strawberry.utils.typing import is_union

from .exceptions import MisplacedFieldError, UnregisteredPydanticTypeError

if TYPE_CHECKING:
    from pydantic.fields import FieldInfo

    from strawberry.exceptions import StrawberryException


class _UnregisteredModel(Exception):
    def __init__(self, model: type[BaseModel]) -> None:
        self.model = model


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

    return next(
        (field for field in definition.fields if field.python_name == field_name),
        None,
    )


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
        raise MisplacedFieldError(field_name=field_name, cls=cls)

    if _contains_strawberry_field(field_info.annotation):
        raise InvalidStrawberryFieldAnnotationError(field_name=field_name, cls=cls)

    strawberry_fields = [
        item for item in field_info.metadata if isinstance(item, StrawberryField)
    ]

    if len(strawberry_fields) > 1:
        raise MultipleStrawberryFieldsError(field_name=field_name, cls=cls)

    return strawberry_fields[0] if strawberry_fields else None


def _replace_pydantic_types(type_: Any, model: type[BaseModel]) -> Any:
    """Replace the pydantic types in `type_` with the types used by Strawberry.

    NewTypes are kept: they're resolved by the schema's scalar registry, like with
    `@strawberry.type`. That's how `strawberry.ID`, `JSON`, `Upload` and
    `scalar_map` scalars work.
    """
    if _is_subclass(type_, BaseModel):
        # `model` can reference itself, but it's only registered after its
        # fields. The definition is inherited by subclasses, which would
        # otherwise be the GraphQL type of their decorated base, and by
        # parametrized generic models, like `Page[User]`
        if type_ is model or "__strawberry_definition__" in vars(type_):
            return type_

        raise _UnregisteredModel(type_)

    origin = get_origin(type_)

    if not origin or not hasattr(type_, "__args__"):
        return type_

    args = tuple(_replace_pydantic_types(arg, model) for arg in get_args(type_))

    if is_union(type_):
        # `X | Y` can't be subscripted, and on python 3.10 forward references
        # don't support `|`
        return Union[args]  # noqa: UP007

    return origin[args]


def _create_strawberry_field(
    cls: type[BaseModel],
    origin: type,
    field_name: str,
    field_info: FieldInfo,
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
        try:
            field_type = _replace_pydantic_types(annotation, model=cls)
        except _UnregisteredModel as exc:
            raise _unregistered_model_error(
                exc.model, cls=origin, field_name=field_name
            ) from None

        strawberry_field.type_annotation = StrawberryAnnotation(
            field_type, namespace=namespace
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


def _unregistered_model_error(
    model: type[BaseModel], *, cls: type, field_name: str
) -> StrawberryException:
    """The error for a field using a model without a GraphQL definition."""
    return UnregisteredPydanticTypeError(model, cls=cls, field_name=field_name)


def get_pydantic_fields(cls: type[BaseModel]) -> list[StrawberryField]:
    """Extract StrawberryFields from a Pydantic BaseModel class.

    Pydantic is the source of truth for which fields exist: its `model_fields`
    already resolved string annotations and merged inherited fields. Fields are
    excluded from the schema when they are marked with `strawberry.Private` or
    with pydantic's `Field(exclude=True)`.

    Fields can be customized using `Annotated`, like with `@strawberry.type`:

    @strawberry.pydantic.type
    class User(BaseModel):
        name: str
        age: Annotated[int, strawberry.field(directives=[SomeDirective()])]

    Args:
        cls: The Pydantic BaseModel class to extract fields from

    Returns:
        List of StrawberryField instances
    """
    fields: list[StrawberryField] = []

    origins = _get_field_origins(cls)

    for field_name, field_info in cls.model_fields.items():
        origin = origins.get(field_name, cls)

        if is_private(field_info.rebuild_annotation()):
            continue

        # `exclude=True` hides a field from pydantic's serialization, so we
        # hide it from the GraphQL output too
        if field_info.exclude is True:
            continue

        if (base_field := _get_strawberry_base_field(origin, field_name)) is not None:
            strawberry_field = base_field
        else:
            strawberry_field = _create_strawberry_field(
                cls, origin, field_name, field_info
            )

        fields.append(strawberry_field)

    return fields


__all__ = ["get_pydantic_fields"]
