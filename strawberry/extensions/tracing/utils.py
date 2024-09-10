from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from strawberry.extensions.utils import is_introspection_field
from strawberry.resolvers import is_default_resolver

if TYPE_CHECKING:
    from graphql import GraphQLResolveInfo


def should_skip_tracing(resolver: Callable[..., Any], info: GraphQLResolveInfo) -> bool:
    if info.field_name not in info.parent_type.fields:
        return True
    resolver = info.parent_type.fields[info.field_name].resolve
    return (
        is_introspection_field(info)
        or is_default_resolver(resolver)
        or resolver is None
    )


__all__ = ["should_skip_tracing"]
