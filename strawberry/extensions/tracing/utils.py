from typing import Callable, List, Union

from graphql import GraphQLResolveInfo

from strawberry.resolvers import is_default_resolver


def is_instrospection_key(key: Union[str, int]) -> bool:
    # from: https://spec.graphql.org/June2018/#sec-Schema
    # > All types and directives defined within a schema must not have a name which
    # > begins with "__" (two underscores), as this is used exclusively
    # > by GraphQL’s introspection system.

    return str(key).startswith("__")


def is_instrospection_field(info: GraphQLResolveInfo) -> bool:
    path = info.path

    while path:
        if is_instrospection_key(path.key):
            return True
        path = path.prev

    return False


def should_skip_tracing(resolver: Callable, info: GraphQLResolveInfo) -> bool:
    if info.field_name not in info.parent_type.fields:
        return True
    resolver = info.parent_type.fields[info.field_name].resolve
    return (
        is_instrospection_field(info)
        or is_default_resolver(resolver)
        or resolver is None
    )


def get_path_from_info(info: GraphQLResolveInfo) -> List[str]:
    path = info.path
    elements = []

    while path:
        elements.append(path.key)
        path = path.prev

    return elements[::-1]
