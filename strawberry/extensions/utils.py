from __future__ import annotations

from typing import TYPE_CHECKING, List, Union

if TYPE_CHECKING:
    from graphql import GraphQLResolveInfo


def is_introspection_key(key: Union[str, int]) -> bool:
    # from: https://spec.graphql.org/June2018/#sec-Schema
    # > All types and directives defined within a schema must not have a name which
    # > begins with "__" (two underscores), as this is used exclusively
    # > by GraphQL`s introspection system.

    return str(key).startswith("__")


def is_introspection_field(info: GraphQLResolveInfo) -> bool:
    path = info.path

    while path:
        if is_introspection_key(path.key):
            return True
        path = path.prev

    return False


def get_path_from_info(info: GraphQLResolveInfo) -> List[str]:
    path = info.path
    elements = []

    while path:
        elements.append(path.key)
        path = path.prev

    return elements[::-1]


__all__ = ["is_introspection_key", "is_introspection_field", "get_path_from_info"]
