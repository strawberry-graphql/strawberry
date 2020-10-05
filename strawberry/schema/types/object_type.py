from typing import Type, cast

from graphql import GraphQLInputObjectType, GraphQLObjectType
from graphql.type.definition import GraphQLInterfaceType

from strawberry.type import TypeDefinition

from .fields import get_field
from .types import ConcreteType, GraphQLType, TypeMap


def _get_object_type_for_type_definition(
    type_definition: TypeDefinition, type_map: TypeMap
) -> GraphQLType:

    if type_definition.name not in type_map:
        TypeClass: Type = GraphQLObjectType

        kwargs = {}

        if type_definition.is_input:
            TypeClass = GraphQLInputObjectType
        elif type_definition.is_interface:
            TypeClass = GraphQLInterfaceType

        if type_definition.interfaces:
            kwargs["interfaces"] = [
                _get_object_type_for_type_definition(interface, type_map)
                for interface in type_definition.interfaces
            ]
            # this tells GraphQL core what the returned object's actual type is
            kwargs["is_type_of"] = lambda obj, _: isinstance(  # type: ignore
                obj, type_definition.origin
            )

        assert not type_definition.is_generic

        object_type = TypeClass(
            name=type_definition.name,
            fields=lambda: {
                field.name: get_field(field, type_definition.is_input, type_map)
                for field in type_definition.fields
            },
            description=type_definition.description,
            **kwargs,
        )

        type_map[type_definition.name] = ConcreteType(
            definition=type_definition, implementation=object_type
        )

    return type_map[type_definition.name].implementation


def get_object_type(origin: Type, type_map: TypeMap) -> GraphQLObjectType:
    """Returns a root type (Query, Mutation, Subscription) from a decorated type"""

    if not hasattr(origin, "_type_definition"):
        raise ValueError(f"Wrong type passed to get object type {origin}")

    type_definition: TypeDefinition = origin._type_definition

    return cast(
        GraphQLObjectType,
        _get_object_type_for_type_definition(type_definition, type_map),
    )
