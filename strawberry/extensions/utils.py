from __future__ import annotations

from typing import TYPE_CHECKING

from strawberry.types.info import Info

if TYPE_CHECKING:
    from graphql import GraphQLResolveInfo
    from graphql.pyutils import Path


def is_introspection_key(key: str | int) -> bool:
    # from: https://spec.graphql.org/June2018/#sec-Schema
    # > All types and directives defined within a schema must not have a name which
    # > begins with "__" (two underscores), as this is used exclusively
    # > by GraphQL`s introspection system.

    return str(key).startswith("__")


def is_introspection_field(info: GraphQLResolveInfo) -> bool:
    path: Path | None = info.path

    while path:
        if is_introspection_key(path.key):
            return True
        path = path.prev

    return False


def get_path_from_info(info: GraphQLResolveInfo) -> list[str | int]:
    path: Path | None = info.path
    elements = []

    while path:
        elements.append(path.key)
        path = path.prev

    return elements[::-1]


def get_graphql_resolve_info(info: GraphQLResolveInfo | Info) -> GraphQLResolveInfo:
    """Return graphql-core's info for a schema extension resolve hook.

    Built-in extensions receive ``GraphQLResolveInfo`` from the middleware, but a
    subclass that annotates ``resolve`` with ``strawberry.Info`` passes the
    Strawberry wrapper when it calls ``super().resolve(...)``.
    """
    if isinstance(info, Info):
        return info._raw_info
    return info


__all__ = [
    "get_graphql_resolve_info",
    "get_path_from_info",
    "is_introspection_field",
    "is_introspection_key",
]
