from typing import Any, Union, cast

from graphql import (
    GraphQLField,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLString,
    GraphQLUnionType,
)
from graphql.type.definition import GraphQLArgument

from strawberry.custom_scalar import ScalarDefinition
from strawberry.enum import EnumDefinition
from strawberry.schema.types.concrete_type import TypeMap
from strawberry.types.types import TypeDefinition
from strawberry.union import StrawberryUnion
from strawberry.utils.inspect import get_func_args

from ..printer import print_schema
from ..schema import Schema as BaseSchema


class Schema(BaseSchema):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._add_scalars()
        self._create_service_field()
        self._extend_query_type()

    def entities_resolver(self, root, info, representations):
        results = []

        for representation in representations:
            type_name = representation.pop("__typename")
            type = self.schema_converter.type_map[type_name]

            definition = cast(TypeDefinition, type.definition)
            resolve_reference = definition.origin.resolve_reference

            func_args = get_func_args(resolve_reference)
            kwargs = representation

            if "info" in func_args:
                kwargs["info"] = info

            results.append(resolve_reference(**kwargs))

        return results

    def _add_scalars(self):
        self.Any = GraphQLScalarType("_Any")

        self._schema.type_map["_Any"] = self.Any

    def _extend_query_type(self):
        fields = {"_service": self._service_field}

        entity_type = _get_entity_type(self.schema_converter.type_map)

        if entity_type:
            self._schema.type_map[entity_type.name] = entity_type

            fields["_entities"] = self._get_entities_field(entity_type)

        query_type = cast(GraphQLObjectType, self._schema.query_type)
        fields.update(query_type.fields)

        self._schema.query_type = GraphQLObjectType(
            name=query_type.name,
            description=query_type.description,
            fields=fields,
        )

        self._schema.type_map["_Service"] = self._service_type
        self._schema.type_map[self._schema.query_type.name] = self._schema.query_type

    def _get_entities_field(self, entity_type: GraphQLUnionType) -> GraphQLField:
        return GraphQLField(
            GraphQLNonNull(GraphQLList(entity_type)),
            args={
                "representations": GraphQLArgument(
                    GraphQLNonNull(GraphQLList(GraphQLNonNull(self.Any)))
                )
            },
            resolve=self.entities_resolver,
        )

    def _create_service_field(self):
        self._service_type = GraphQLObjectType(
            name="_Service", fields={"sdl": GraphQLField(GraphQLNonNull(GraphQLString))}
        )

        self._service_field = GraphQLField(
            GraphQLNonNull(self._service_type),
            resolve=lambda _, info: {"sdl": print_schema(self)},
        )


def _get_entity_type(type_map: TypeMap):
    # https://www.apollographql.com/docs/apollo-server/federation/federation-spec/#resolve-requests-for-entities

    # To implement the _Entity union, each type annotated with @key
    # should be added to the _Entity union.

    federation_key_types = [
        type.implementation
        for type in type_map.values()
        if _has_federation_keys(type.definition)
    ]

    # If no types are annotated with the key directive, then the _Entity
    # union and Query._entities field should be removed from the schema.
    if not federation_key_types:
        return None

    entity_type = GraphQLUnionType("_Entity", federation_key_types)  # type: ignore

    def _resolve_type(self, value, _type):
        return self._type_definition.name

    entity_type.resolve_type = _resolve_type

    return entity_type


def _is_key(directive: Any) -> bool:
    from .schema_directives import Key

    return isinstance(directive, Key)


def _has_federation_keys(
    definition: Union[TypeDefinition, ScalarDefinition, EnumDefinition, StrawberryUnion]
) -> bool:
    if isinstance(definition, TypeDefinition):
        return any(_is_key(directive) for directive in definition.directives or [])

    return False
