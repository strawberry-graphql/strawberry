import typing
from itertools import islice

from graphql import DirectiveLocation, GraphQLArgument, GraphQLDirective

from .type_converter import get_graphql_type_for_annotation
from .utils.str_converters import to_camel_case


DIRECTIVE_REGISTRY = {}


def _get_arguments(func):
    annotations = func.__annotations__

    arguments = {}

    for name, type_ in islice(annotations.items(), 1, None):
        if name == "return":
            continue

        argument_type = get_graphql_type_for_annotation(type_, name)

        name = to_camel_case(name)

        arguments[name] = GraphQLArgument(argument_type)

    return arguments


def directive(
    *, locations: typing.List[DirectiveLocation], description=None, name=None
):
    def _wrap(func):
        directive_name = name or to_camel_case(func.__name__)

        func.directive = GraphQLDirective(
            name=directive_name,
            locations=locations,
            args=_get_arguments(func),
            description=description,
        )

        DIRECTIVE_REGISTRY[directive_name] = func

        return func

    return _wrap
