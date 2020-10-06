from typing import Dict, List, cast

from graphql import GraphQLArgument, Undefined
from graphql.type.definition import GraphQLInputType

from strawberry.arguments import ArgumentDefinition, undefined

from .type import get_graphql_type
from .types import TypeMap


def convert_argument(
    argument: ArgumentDefinition, type_map: TypeMap
) -> GraphQLArgument:
    # TODO: test and support generic arguments?
    default_value = (
        Undefined if argument.default_value is undefined else argument.default_value
    )

    # TODO: we could overload the function to tell mypy that it returns input types too
    argument_type = cast(GraphQLInputType, get_graphql_type(argument, type_map))

    return GraphQLArgument(argument_type, default_value=default_value)


def convert_arguments(
    arguments: List[ArgumentDefinition], type_map: TypeMap
) -> Dict[str, GraphQLArgument]:
    arguments_dict = {}

    for argument in arguments:
        name = cast(str, argument.name)
        arguments_dict[name] = convert_argument(argument, type_map)

    return arguments_dict
