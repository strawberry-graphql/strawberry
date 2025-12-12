from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from graphql import GraphQLResolveInfo

    from strawberry.types.info import Info

    # Accept both Info and GraphQLResolveInfo for backwards compatibility
    InfoType = Info | GraphQLResolveInfo


def is_introspection_key(key: str | int) -> bool:
    # from: https://spec.graphql.org/June2018/#sec-Schema
    # > All types and directives defined within a schema must not have a name which
    # > begins with "__" (two underscores), as this is used exclusively
    # > by GraphQL`s introspection system.

    return str(key).startswith("__")


def is_introspection_field(info: InfoType) -> bool:
    # Handle both Info and GraphQLResolveInfo
    path = info.path

    while path:
        if is_introspection_key(path.key):
            return True
        path = path.prev

    return False


def get_path_from_info(info: InfoType) -> list[str]:
    # Handle both Info and GraphQLResolveInfo
    path = info.path
    elements = []

    while path:
        elements.append(path.key)
        path = path.prev

    return elements[::-1]


__all__ = ["get_path_from_info", "is_introspection_field", "is_introspection_key"]
