"""Converting between pydantic models and GraphQL input values."""

from __future__ import annotations

from collections import abc
from typing import TYPE_CHECKING, Annotated, Any, TypeGuard, get_args, get_origin

from pydantic import (
    BaseModel,
    InstanceOf,
    PlainValidator,
    SkipValidation,
    ValidationError,
)

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

    from pydantic.fields import FieldInfo

    from strawberry.types.arguments import InputContext
    from strawberry.types.base import StrawberryType

# Annotations that make pydantic validate a field without validating its model
_NOT_VALIDATED_AS_MODEL = (InstanceOf, PlainValidator, SkipValidation)

# Generics Strawberry exposes as GraphQL lists (see `StrawberryAnnotation._is_list`)
# whose items pydantic validates as their type. Subclasses of `list` are GraphQL
# lists too, but pydantic only validates their items with a core schema they define
_LIST_ORIGINS = (list, tuple, abc.Sequence)


def _skips_model_validation(metadata: object) -> bool:
    # `SkipValidation` and `InstanceOf` also work as bare classes, as in
    # `Annotated[Model, SkipValidation]`
    return isinstance(metadata, _NOT_VALIDATED_AS_MODEL) or (
        isinstance(metadata, type) and issubclass(metadata, _NOT_VALIDATED_AS_MODEL)
    )


def _is_validated_as(annotation: Any, model: type[BaseModel]) -> bool:
    if annotation is model:
        return True

    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin is Annotated:
        return not any(
            _skips_model_validation(item) for item in args[1:]
        ) and _is_validated_as(args[0], model)

    if is_union(annotation):
        types = [arg for arg in args if arg is not type(None)]

        return len(types) == 1 and _is_validated_as(types[0], model)

    # pydantic validates the items of bare `typing.List` and `typing.Sequence`
    # as `Any`
    if origin in _LIST_ORIGINS and args:
        return _is_validated_as(args[0], model)

    return False


def _validates_field_as(field_info: FieldInfo | None, model: type[BaseModel]) -> bool:
    """Return whether pydantic validates the field's values as `model`.

    For example, a field annotated with `SkipValidation[Model]` or a base class of
    `model` isn't.
    """
    return (
        field_info is not None
        and not any(_skips_model_validation(item) for item in field_info.metadata)
        and _is_validated_as(field_info.annotation, model)
    )


def _is_nested_model(
    type_: object, field_info: FieldInfo | None
) -> TypeGuard[type[BaseModel]]:
    """Return whether `type_` is a model pydantic validates as part of the field.

    Values of nested models are passed to pydantic as data, so that they're
    validated with the outermost model and all their errors are reported, with
    their full location.
    """
    return (
        isinstance(type_, type)
        and issubclass(type_, BaseModel)
        and _validates_field_as(field_info, type_)
    )


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

        if graphql_name in value:
            data[field.python_name] = _to_python_value(
                value[graphql_name],
                field.resolve_type(type_definition=definition),
                field_info,
                context,
                (*keys, graphql_name),
            )
        # nullable fields are optional for clients, like in other input types, so
        # pydantic gets `None` for a missing one it requires, e.g. `str | None`
        # without a default (GraphQL validates that non-null fields are sent)
        elif field_info is not None and field_info.is_required():
            data[field.python_name] = None

    return data


def _to_python_value(
    value: Any,
    type_: StrawberryType | type,
    field_info: FieldInfo | None,
    context: InputContext,
    keys: tuple[str | int, ...],
) -> Any:
    if value is None:
        return None

    if isinstance(type_, StrawberryOptional):
        return _to_python_value(value, type_.of_type, field_info, context, keys)

    if isinstance(type_, StrawberryList):
        # only lists of nested models are converted item by item, other lists
        # are converted at once like Strawberry does, which e.g. only copies
        # lists of scalars
        if not _is_nested_model(_get_item_type(type_), field_info):
            return context.convert(value, type_, *keys)

        return [
            _to_python_value(item, type_.of_type, field_info, context, (*keys, index))
            for index, item in enumerate(value)
        ]

    if isinstance(type_, LazyType):
        return _to_python_value(value, type_.resolve_type(), field_info, context, keys)

    if _is_nested_model(type_, field_info) and not isinstance(value, type_):
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
    return {
        name: getattr(model, name)
        for name in type(model).model_fields
        if name in model.model_fields_set
    }


def build_pydantic_model(
    model: type[BaseModel], value: Mapping[str, Any], context: InputContext
) -> BaseModel:
    """The `from_input` hook of `strawberry.pydantic` types."""
    data = _to_python_data(model, value, context, ())

    validation_context: dict[str, Any] = {}

    if context.info is not None:
        validation_context["info"] = context.info

        if context.info.context is not None:
            validation_context["strawberry_context"] = context.info.context

    try:
        # the data uses the fields' python names, aliases would match a field
        # whose alias is the python name of another one
        result = model.model_validate(
            data,
            context=validation_context or None,
            by_alias=False,
            by_name=True,
        )
    except ValidationError as exc:
        issues = [
            ValidationIssue(
                location=_get_location(model, error["loc"], context),
                message=error["msg"],
                type=error["type"],
            )
            for error in exc.errors(include_url=False, include_input=False)
        ]
    else:
        return result

    # pydantic's error isn't chained, as its message includes the input values,
    # which would end up in the logs
    raise InputValidationError(issues) from None
