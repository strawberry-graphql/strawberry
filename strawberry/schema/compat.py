from __future__ import annotations

from typing import TYPE_CHECKING

from strawberry.scalars import is_scalar as is_strawberry_scalar
from strawberry.types.base import (
    StrawberryType,
    has_object_definition,
)

# TypeGuard is only available in typing_extensions => 3.10, we don't want
# to force updates to the typing_extensions package so we only use it when
# TYPE_CHECKING is enabled.

if TYPE_CHECKING:
    from collections.abc import Mapping
    from typing import TypeGuard

    from strawberry.types.scalar import ScalarDefinition, ScalarWrapper


def is_input_type(type_: StrawberryType | type) -> TypeGuard[type]:
    if not has_object_definition(type_):
        return False
    return type_.__strawberry_definition__.is_input


def is_interface_type(type_: StrawberryType | type) -> TypeGuard[type]:
    if not has_object_definition(type_):
        return False
    return type_.__strawberry_definition__.is_interface


def is_scalar(
    type_: StrawberryType | type,
    scalar_registry: Mapping[object, ScalarWrapper | ScalarDefinition],
) -> TypeGuard[type]:
    return is_strawberry_scalar(type_, scalar_registry)


def is_schema_directive(type_: StrawberryType | type) -> TypeGuard[type]:
    return hasattr(type_, "__strawberry_directive__")


# TODO: do we still need this?
def is_graphql_generic(type_: StrawberryType | type) -> bool:
    if has_object_definition(type_):
        return type_.__strawberry_definition__.is_graphql_generic

    if isinstance(type_, StrawberryType):
        return type_.is_graphql_generic

    return False


__all__ = [
    "is_graphql_generic",
    "is_input_type",
    "is_interface_type",
    "is_scalar",
    "is_schema_directive",
]
