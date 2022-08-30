from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional, Union

from strawberry.custom_scalar import ScalarDefinition
from strawberry.scalars import is_scalar as is_strawberry_scalar
from strawberry.type import StrawberryType
from strawberry.types.types import (
    TemplateTypeDefinition,
    TypeDefinition,
    get_type_definition,
)


# TypeGuard is only available in typing_extensions => 3.10, we don't want
# to force updates to the typing_extensions package so we only use it when
# TYPE_CHECKING is enabled.

if TYPE_CHECKING:
    from typing_extensions import TypeGuard


def is_input_type(type_: Union[StrawberryType, type]) -> TypeGuard[type]:
    if not is_object_type(type_):
        return False

    type_definition: TypeDefinition = type_._type_definition  # type: ignore
    return type_definition.is_input


def is_interface_type(type_: Union[StrawberryType, type]) -> Optional[TypeDefinition]:
    if definition := get_type_definition(type_):
        if definition.is_interface:
            return definition
    return None


def is_scalar(
    type_: Union[StrawberryType, type],
    scalar_registry: Dict[object, ScalarDefinition],
) -> TypeGuard[type]:
    # isinstance(type_, StrawberryScalar)  # noqa: E800
    return is_strawberry_scalar(type_, scalar_registry)


def is_object_type(type_: Union[StrawberryType, type]) -> Optional[TypeDefinition]:
    return get_type_definition(type_)


def is_enum(type_: Union[StrawberryType, type]) -> TypeGuard[type]:
    # isinstance(type_, StrawberryEnumType)  # noqa: E800
    return hasattr(type_, "_enum_definition")


def is_generic(type_: Union[StrawberryType, type]) -> bool:
    if definition := get_type_definition(type_):
        return isinstance(definition, TemplateTypeDefinition)
    return False
