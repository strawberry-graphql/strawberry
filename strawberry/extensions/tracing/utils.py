from typing import Callable

from graphql import GraphQLResolveInfo

from strawberry.extensions.utils import is_introspection_field
from strawberry.resolvers import is_default_resolver


def should_skip_tracing(resolver: Callable, info: GraphQLResolveInfo) -> bool:
    if info.field_name not in info.parent_type.fields:
        return True
    resolver = info.parent_type.fields[info.field_name].resolve
    return (
        is_introspection_field(info)
        or is_default_resolver(resolver)
        or resolver is None
    )
