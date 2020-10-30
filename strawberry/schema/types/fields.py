import typing

from graphql import GraphQLField, GraphQLInputField

from strawberry.arguments import UNSET
from strawberry.field import FieldDefinition
from strawberry.resolvers import get_resolver
from strawberry.types.types import undefined

from .arguments import convert_arguments
from .type import get_graphql_type
from .types import Field, TypeMap


def get_field(
    field: FieldDefinition,
    is_input: bool,
    type_map: TypeMap,
    auto_camel_case: bool,
) -> Field:
    graphql_type = get_graphql_type(field, type_map, auto_camel_case=auto_camel_case)

    TypeClass: typing.Union[
        typing.Type[GraphQLInputField], typing.Type[GraphQLField]
    ] = GraphQLField

    kwargs: typing.Dict[str, typing.Any] = {
        "description": field.description,
    }

    resolver = get_resolver(field, auto_camel_case=auto_camel_case)

    if is_input:
        TypeClass = GraphQLInputField
        if field.default_value not in (undefined, UNSET):
            kwargs["default_value"] = field.default_value
    elif field.is_subscription:
        kwargs["args"] = convert_arguments(
            field.arguments, type_map, auto_camel_case=auto_camel_case
        )
        kwargs["subscribe"] = resolver
        kwargs["resolve"] = lambda event, *args, **kwargs: event
    else:
        kwargs["args"] = convert_arguments(
            field.arguments, type_map, auto_camel_case=auto_camel_case
        )
        kwargs["resolve"] = resolver

    if not is_input:
        kwargs["deprecation_reason"] = field.deprecation_reason

    return TypeClass(graphql_type, **kwargs)  # type: ignore
