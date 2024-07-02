from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Union

from strawberry.scalars import is_scalar as is_strawberry_scalar
from strawberry.type import StrawberryType, has_object_definition

# TypeGuard is only available in typing_extensions => 3.10, we don't want
# to force updates to the typing_extensions package so we only use it when
# TYPE_CHECKING is enabled.

if TYPE_CHECKING:
    from typing_extensions import TypeGuard

    from strawberry.custom_scalar import ScalarDefinition, ScalarWrapper


def is_input_type(type_: Union[StrawberryType, type]) -> TypeGuard[type]:
    if not has_object_definition(type_):
        return False
    return type_.__strawberry_definition__.is_input


def is_interface_type(type_: Union[StrawberryType, type]) -> TypeGuard[type]:
    if not has_object_definition(type_):
        return False
    return type_.__strawberry_definition__.is_interface


def is_scalar(
    type_: Union[StrawberryType, type],
    scalar_registry: Dict[object, Union[ScalarWrapper, ScalarDefinition]],
) -> TypeGuard[type]:
    return is_strawberry_scalar(type_, scalar_registry)


def is_enum(type_: Union[StrawberryType, type]) -> TypeGuard[type]:
    return hasattr(type_, "_enum_definition")


def is_schema_directive(type_: Union[StrawberryType, type]) -> TypeGuard[type]:
    return hasattr(type_, "__strawberry_directive__")


# TODO: do we still need this?
def is_graphql_generic(type_: Union[StrawberryType, type]) -> bool:
    if has_object_definition(type_):
        return type_.__strawberry_definition__.is_graphql_generic

    if isinstance(type_, StrawberryType):
        return type_.is_graphql_generic

    return False
