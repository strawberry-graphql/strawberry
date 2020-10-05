from typing import cast

from graphql import GraphQLEnumType, GraphQLEnumValue

from strawberry.enum import EnumDefinition

from .types import ConcreteType, TypeMap


def get_enum_type(
    enum_definition: EnumDefinition, type_map: TypeMap
) -> GraphQLEnumType:
    if enum_definition.name not in type_map:
        enum = GraphQLEnumType(
            name=enum_definition.name,
            values={
                item.name: GraphQLEnumValue(item.value)
                for item in enum_definition.values
            },
            description=enum_definition.description,
        )

        type_map[enum_definition.name] = ConcreteType(
            definition=enum_definition, implementation=enum
        )

    return cast(GraphQLEnumType, type_map[enum_definition.name].implementation)
