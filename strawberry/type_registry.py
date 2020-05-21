import typing

from graphql import (
    GraphQLBoolean,
    GraphQLFloat,
    GraphQLID,
    GraphQLInt,
    GraphQLString,
    GraphQLType,
)

from .scalars import ID


TYPE_HINTS_REGISTRY: typing.Dict[str, typing.Type] = {}
ANNOTATION_REGISTRY: typing.Dict[typing.Type, GraphQLType] = {
    str: GraphQLString,
    int: GraphQLInt,
    float: GraphQLFloat,
    bool: GraphQLBoolean,
    ID: GraphQLID,
}

GRAPHQL_TYPE_TO_STRAWBERRY_TYPE: typing.Dict[GraphQLType, typing.Type] = {}


def register_type(
    cls: typing.Type, graphql_type: GraphQLType, *, store_type_information: bool = True
) -> None:
    """Register a Strawberry type alongside its GraphQL type"""

    # register the annotation so we can use when getting the graphql type for
    # an annotation in type_converter
    ANNOTATION_REGISTRY[cls] = graphql_type
    GRAPHQL_TYPE_TO_STRAWBERRY_TYPE[graphql_type] = cls

    # register names to classes so that we can pass them to get_type_hints
    TYPE_HINTS_REGISTRY[cls.__name__] = cls

    # we currently have to store the "graphql core" type onto the
    # class, but we can't do that for all types (like builtins),
    # so we have an escape hatch for that

    if store_type_information:
        cls.graphql_type = graphql_type


def get_strawberry_type_for_graphql_type(
    graphql_type: GraphQLType,
) -> typing.Optional[typing.Type]:
    return GRAPHQL_TYPE_TO_STRAWBERRY_TYPE.get(graphql_type)


def get_type_for_annotation(annotation: typing.Type) -> typing.Optional[GraphQLType]:
    return ANNOTATION_REGISTRY.get(annotation)


def get_registered_types() -> typing.Dict[str, typing.Type]:
    return TYPE_HINTS_REGISTRY
