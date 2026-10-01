"""Building pydantic models from GraphQL input values."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, get_args, get_origin

from pydantic import BaseModel, InstanceOf, PlainValidator, SkipValidation

from strawberry.types.base import StrawberryList, StrawberryOptional
from strawberry.types.lazy_type import LazyType
from strawberry.utils.typing import is_union

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pydantic.fields import FieldInfo

    from strawberry.types.arguments import InputContext
    from strawberry.types.base import StrawberryType

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
    model: type[BaseModel], value: Mapping[str, Any], context: InputContext
) -> dict[str, Any]:
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
            )

    return data


def _to_python_value(
    value: Any,
    type_: StrawberryType | type,
    field_info: FieldInfo | None,
    context: InputContext,
) -> Any:
    if value is None:
        return None

    if isinstance(type_, StrawberryOptional):
        return _to_python_value(value, type_.of_type, field_info, context)

    if isinstance(type_, StrawberryList):
        return [
            _to_python_value(item, type_.of_type, field_info, context) for item in value
        ]

    if isinstance(type_, LazyType):
        return _to_python_value(value, type_.resolve_type(), field_info, context)

    # nested models are validated with the outermost one, so that all their
    # errors are reported, with their full location
    if (
        isinstance(type_, type)
        and issubclass(type_, BaseModel)
        and not isinstance(value, type_)
        and _validates_field_as(field_info, type_)
    ):
        return _to_python_data(type_, value, context)

    return context.convert(value, type_)


def build_pydantic_model(
    model: type[BaseModel], value: Mapping[str, Any], context: InputContext
) -> BaseModel:
    """The `from_input` hook of `strawberry.pydantic` types."""
    data = _to_python_data(model, value, context)

    validation_context: dict[str, Any] = {}

    if context.info is not None:
        validation_context["info"] = context.info

        if context.info.context is not None:
            validation_context["strawberry_context"] = context.info.context

    # the data uses the fields' python names, not their aliases
    return model.model_validate(data, context=validation_context or None, by_name=True)
