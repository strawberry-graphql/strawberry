"""Converting between pydantic models and GraphQL input values."""

from __future__ import annotations

from collections import abc
from typing import TYPE_CHECKING, Annotated, Any, TypeGuard, get_args, get_origin

from pydantic import BaseModel, ValidationError

from strawberry.types.base import (
    StrawberryList,
    StrawberryOptional,
    get_object_definition,
)
from strawberry.types.lazy_type import LazyType
from strawberry.utils.typing import is_union

from .error import InputValidationError, ValidationIssue

if TYPE_CHECKING:
    from collections.abc import Mapping

    from strawberry.types.arguments import InputContext
    from strawberry.types.base import StrawberryType

# Generics Strawberry exposes as GraphQL lists (see `StrawberryAnnotation._is_list`)
# whose items pydantic validates as their type. Subclasses of `list` are GraphQL
# lists too, but pydantic only validates their items with a core schema they define
_LIST_ORIGINS = (list, tuple, abc.Sequence)


def _is_nested_model(type_: object) -> TypeGuard[type[BaseModel]]:
    """Return whether `type_` is a pydantic model.

    Nested inputs are always passed as data. The outermost model's annotations
    and validators, not the GraphQL types, decide how that data is validated.
    """
    return isinstance(type_, type) and issubclass(type_, BaseModel)


def _unwrap_annotation(annotation: Any) -> Any:
    """Return `annotation` without `Annotated` and `None`.

    e.g. `list[int]` for `Annotated[list[int] | None, Field(min_length=1)]`.
    """
    while True:
        if get_origin(annotation) is Annotated:
            annotation = get_args(annotation)[0]
        elif is_union(annotation):
            types = [arg for arg in get_args(annotation) if arg is not type(None)]

            if len(types) != 1:
                return annotation

            annotation = types[0]
        else:
            return annotation


def _is_tuple(annotation: Any) -> bool:
    return annotation is tuple or get_origin(annotation) is tuple


def _has_tuples(annotation: Any) -> bool:
    """Return whether pydantic validates a GraphQL list, or lists in it, as tuples."""
    annotation = _unwrap_annotation(annotation)

    if _is_tuple(annotation):
        return True

    args = get_args(annotation)

    return (
        get_origin(annotation) in _LIST_ORIGINS and bool(args) and _has_tuples(args[0])
    )


def _to_tuples(value: Any, annotation: Any) -> Any:
    """Convert the lists in `value` that pydantic validates as tuples to tuples.

    GraphQL lists are converted to lists, but in strict mode pydantic only
    accepts tuples for tuple fields.
    """
    if not isinstance(value, list):
        return value

    annotation = _unwrap_annotation(annotation)
    args = get_args(annotation)
    # like Strawberry, which exposes `tuple[int, int]` as a list of `Int`
    item_annotation = args[0] if args else Any
    items = [_to_tuples(item, item_annotation) for item in value]

    return tuple(items) if _is_tuple(annotation) else items


def _get_item_type(type_: StrawberryList) -> StrawberryType | type:
    """Return the type of the innermost items of a list, e.g. of nested lists."""
    item_type = type_.of_type

    while isinstance(item_type, (StrawberryOptional, StrawberryList, LazyType)):
        item_type = (
            item_type.resolve_type()
            if isinstance(item_type, LazyType)
            else item_type.of_type
        )

    return item_type


def _to_python_data(
    model: type[BaseModel],
    value: Mapping[str, Any],
    context: InputContext,
    keys: tuple[str | int, ...],
) -> dict[str, Any]:
    """Convert `value` to the data pydantic validates `model` with.

    `keys` are the location of `value` in the outermost input.
    """
    definition = model.__strawberry_definition__  # type: ignore[attr-defined]
    data: dict[str, Any] = {}

    for field in definition.fields:
        graphql_name = context.config.name_converter.from_field(field)
        field_info = model.model_fields.get(field.python_name)
        field_type = field.resolve_type(type_definition=definition)

        if graphql_name in value:
            python_value = _to_python_value(
                value[graphql_name],
                field_type,
                context,
                (*keys, graphql_name),
            )

            if field_info is not None and _has_tuples(field_info.annotation):
                python_value = _to_tuples(python_value, field_info.annotation)

            data[field.python_name] = python_value
        # nullable fields are optional for clients, like in other input types, so
        # pydantic gets `None` for a missing one it requires, e.g. `str | None`
        # without a default
        elif (
            field_info is not None
            and field_info.is_required()
            and isinstance(field_type, StrawberryOptional)
        ):
            data[field.python_name] = None

    return data


def _to_python_value(
    value: Any,
    type_: StrawberryType | type,
    context: InputContext,
    keys: tuple[str | int, ...],
) -> Any:
    if value is None:
        return None

    if isinstance(type_, StrawberryOptional):
        return _to_python_value(value, type_.of_type, context, keys)

    if isinstance(type_, StrawberryList):
        # only lists of nested models are converted item by item, other lists
        # are converted at once like Strawberry does, which e.g. only copies
        # lists of scalars
        if not _is_nested_model(_get_item_type(type_)):
            return context.convert(value, type_, *keys)

        return [
            _to_python_value(item, type_.of_type, context, (*keys, index))
            for index, item in enumerate(value)
        ]

    if isinstance(type_, LazyType):
        return _to_python_value(value, type_.resolve_type(), context, keys)

    if _is_nested_model(type_) and not isinstance(value, type_):
        return _to_python_data(type_, value, context, keys)

    return context.convert(value, type_, *keys)


def _get_location(
    model: type[BaseModel], loc: tuple[str | int, ...], context: InputContext
) -> list[str]:
    """Map a pydantic error location to the GraphQL names the client used.

    The location stops at the deepest value that can be located in GraphQL, so
    it doesn't include e.g. union tags, dictionary keys or private fields.
    """
    location = [str(segment) for segment in context.path]
    type_: StrawberryType | type = model

    for segment in loc:
        while isinstance(type_, (StrawberryOptional, LazyType)):
            type_ = (
                type_.resolve_type() if isinstance(type_, LazyType) else type_.of_type
            )

        if isinstance(type_, StrawberryList):
            if not isinstance(segment, int):
                break

            location.append(str(segment))
            type_ = type_.of_type

            continue

        definition = get_object_definition(type_)
        field = (
            definition.get_field(segment)
            if definition is not None and isinstance(segment, str)
            else None
        )

        if field is None:
            break

        location.append(context.config.name_converter.from_field(field))
        type_ = field.resolve_type(type_definition=definition)

    return location


def dump_pydantic_model(model: BaseModel) -> dict[str, Any]:
    """The `to_input` hook of `strawberry.pydantic` inputs.

    A model used as a default only includes the fields that were set on it, like
    the data a client sends, so that the model built from the default has the
    same `model_fields_set`.
    """
    # the values are read like `model_dump` does, as reading a deprecated field
    # with `getattr` emits pydantic's warning
    return {
        name: model.__dict__[name]
        for name in type(model).model_fields
        if name in model.model_fields_set
    }


def build_pydantic_model(
    model: type[BaseModel], value: Mapping[str, Any], context: InputContext
) -> BaseModel:
    """The `from_input` hook of `strawberry.pydantic` inputs."""
    data = _to_python_data(model, value, context, ())

    try:
        # the data uses the fields' python names, aliases would match a field
        # whose alias is the python name of another one
        result = model.model_validate(
            data,
            by_alias=False,
            by_name=True,
        )
    except ValidationError as exc:
        issues = [
            ValidationIssue(
                location=_get_location(model, error["loc"], context),
                message=(
                    str(error["ctx"]["error"])
                    if error["type"] == "value_error"
                    and isinstance(error.get("ctx", {}).get("error"), ValueError)
                    else error["msg"]
                ),
                type=error["type"],
            )
            for error in exc.errors(include_url=False, include_input=False)
        ]
    else:
        return result

    # Don't chain pydantic's error, whose rendering includes input values.
    # Removing Pydantic's ValueError prefix does not redact messages, which
    # may contain values included by pydantic or user-defined validators.
    raise InputValidationError(issues) from None
