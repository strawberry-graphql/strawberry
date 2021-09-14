from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Union, cast

from strawberry.enum import EnumDefinition
from strawberry.type import StrawberryList, StrawberryOptional, StrawberryType

from .exceptions import UnsupportedTypeError
from .scalars import is_scalar
from .types.arguments import (
    UNSET,
    StrawberryArgument,
    StrawberryArgumentAnnotation,
    is_unset,
)
from .types.types import TypeDefinition


def convert_argument(
    value: object, type_: Union[StrawberryType, type], auto_camel_case: bool = True
) -> object:
    if value is None:
        return None

    if is_unset(value):
        return value

    if isinstance(type_, StrawberryOptional):
        return convert_argument(value, type_.of_type)

    if isinstance(type_, StrawberryList):
        value_list = cast(Iterable, value)
        return [convert_argument(x, type_.of_type) for x in value_list]

    if is_scalar(type_):
        return value

    # Convert Enum fields to instances using the value. This is safe
    # because graphql-core has already validated the input.
    if isinstance(type_, EnumDefinition):
        return type_.wrapped_cls(value)

    if hasattr(type_, "_type_definition"):  # TODO: Replace with StrawberryInputObject
        type_definition: TypeDefinition = type_._type_definition  # type: ignore

        assert type_definition.is_input

        kwargs = {}

        for field in type_definition.fields:
            value = cast(Mapping, value)
            graphql_name = field.get_graphql_name(auto_camel_case)

            if graphql_name in value:
                kwargs[field.python_name] = convert_argument(
                    value[graphql_name], field.type, auto_camel_case
                )

        type_ = cast(type, type_)
        return type_(**kwargs)

    raise UnsupportedTypeError(type_)


def convert_arguments(
    value: Dict[str, Any],
    arguments: List[StrawberryArgument],
    auto_camel_case: bool = True,
) -> Dict[str, Any]:
    """Converts a nested dictionary to a dictionary of actual types.

    It deals with conversion of input types to proper dataclasses and
    also uses a sentinel value for unset values."""

    if not arguments:
        return {}

    kwargs = {}

    for argument in arguments:
        assert argument.python_name

        name = argument.get_graphql_name(auto_camel_case)

        if name in value:
            current_value = value[name]

            kwargs[argument.python_name] = convert_argument(
                value=current_value,
                type_=argument.type,
                auto_camel_case=auto_camel_case,
            )

    return kwargs


def argument(
    description: Optional[str] = None, name: Optional[str] = None
) -> StrawberryArgumentAnnotation:
    return StrawberryArgumentAnnotation(description=description, name=name)


# TODO: check exports
__all__ = [
    "StrawberryArgument",
    "StrawberryArgumentAnnotation",
    "UNSET",
    "argument",
    "is_unset",
]


__all__ = ["convert_argument", "convert_arguments", "argument", "UNSET"]
