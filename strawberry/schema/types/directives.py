import inspect
import typing
from itertools import islice

from graphql import GraphQLDirective

from strawberry.arguments import ArgumentDefinition, get_arguments_from_annotations

from .arguments import convert_arguments
from .types import TypeMap


def get_arguments_for_directive(
    resolver: typing.Callable,
) -> typing.List[ArgumentDefinition]:
    # TODO: move this into directive declaration
    annotations = resolver.__annotations__
    annotations = dict(islice(annotations.items(), 1, None))
    annotations.pop("return", None)

    parameters = inspect.signature(resolver).parameters

    return get_arguments_from_annotations(annotations, parameters, origin=resolver)


def get_directive_type(origin: typing.Any, type_map: TypeMap) -> GraphQLDirective:
    if not hasattr(origin, "directive_definition"):
        raise ValueError(f"Wrong type passed to get directive type {origin}")

    return GraphQLDirective(
        name=origin.directive_definition.name,
        locations=origin.directive_definition.locations,
        description=origin.directive_definition.description,
        args=convert_arguments(
            get_arguments_for_directive(origin.directive_definition.resolver), type_map
        ),
    )
