"""Building pydantic models from GraphQL input values."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, get_args, get_origin

from pydantic import (
    AliasChoices,
    AliasPath,
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
    from strawberry.types.base import StrawberryObjectDefinition, StrawberryType
    from strawberry.types.field import StrawberryField

# Annotations that make pydantic validate a field without validating its model
_NOT_VALIDATED_AS_MODEL = (InstanceOf, PlainValidator, SkipValidation)


def _is_validated_as(annotation: Any, model: type[BaseModel]) -> bool:
    if annotation is model:
        return True

    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin is Annotated:
        return not any(
            isinstance(item, _NOT_VALIDATED_AS_MODEL) for item in args[1:]
        ) and _is_validated_as(args[0], model)

    if is_union(annotation):
        types = [arg for arg in args if arg is not type(None)]

        return len(types) == 1 and _is_validated_as(types[0], model)

    if origin in (list, tuple):
        return _is_validated_as(args[0], model)

    return False


def _validates_field_as(field_info: FieldInfo | None, model: type[BaseModel]) -> bool:
    """Return whether pydantic validates the field's values as `model`.

    For example, a field annotated with `SkipValidation[Model]` or a base class of
    `model` isn't.
    """
    return (
        field_info is not None
        and not any(
            isinstance(item, _NOT_VALIDATED_AS_MODEL) for item in field_info.metadata
        )
        and _is_validated_as(field_info.annotation, model)
    )


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

        if graphql_name in value:
            data[field.python_name] = _to_python_value(
                value[graphql_name],
                field.resolve_type(type_definition=definition),
                model.model_fields.get(field.python_name),
                context,
                (*keys, graphql_name),
            )

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
        return [
            _to_python_value(item, type_.of_type, field_info, context, (*keys, index))
            for index, item in enumerate(value)
        ]

    if isinstance(type_, LazyType):
        return _to_python_value(value, type_.resolve_type(), field_info, context, keys)

    # nested models are validated with the outermost one, so that all their
    # errors are reported, with their full location
    if (
        isinstance(type_, type)
        and issubclass(type_, BaseModel)
        and not isinstance(value, type_)
        and _validates_field_as(field_info, type_)
    ):
        return _to_python_data(type_, value, context, keys)

    return context.convert(value, type_, *keys)


def _get_pydantic_keys(field_info: FieldInfo) -> set[str]:
    """Keys pydantic can use in error locations for a field, besides its name."""
    keys = set()

    for alias in (field_info.alias, field_info.validation_alias):
        choices = alias.choices if isinstance(alias, AliasChoices) else [alias]

        for choice in choices:
            key = choice.path[0] if isinstance(choice, AliasPath) else choice

            if isinstance(key, str):
                keys.add(key)

    return keys


def _find_field(
    definition: StrawberryObjectDefinition, segment: str
) -> StrawberryField | None:
    if field := definition.get_field(segment):
        return field

    # e.g. missing fields are reported with their alias
    if isinstance(definition.origin, type) and issubclass(definition.origin, BaseModel):
        model_fields = definition.origin.model_fields

        for field in definition.fields:
            field_info = model_fields.get(field.python_name)

            if field_info is not None and segment in _get_pydantic_keys(field_info):
                return field

    return None


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
            _find_field(definition, segment)
            if definition is not None and isinstance(segment, str)
            else None
        )

        if field is None:
            break

        location.append(context.config.name_converter.from_field(field))
        type_ = field.resolve_type(type_definition=definition)

    return location


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
