from typing import Any, Dict, Optional

from graphql import GraphQLArgument, GraphQLEnumType, GraphQLField, \
    GraphQLInterfaceType, GraphQLObjectType, GraphQLSchema, GraphQLType, \
    Undefined

from strawberry.types import StrawberryArgument, StrawberryEnum, \
    StrawberryField, StrawberryInterface, StrawberryObject, StrawberryObjectType


class GraphQLCoreConverter:

    def __init__(self):
        self._type_map: Dict[StrawberryObject, GraphQLType] = {}

    def to_argument(self, argument: StrawberryArgument) -> GraphQLArgument:
        ...

        graphql_type = ...
        graphql_default_value = self.to_default_value(argument.default_value)

        graphql_argument = GraphQLArgument(
            type_=graphql_type,
            default_value=graphql_default_value,
            description=argument.description,
            out_name=...,
            extensions=...,
            ast_node=...
        )

        return graphql_argument

    def to_default_value(self, value: Any) -> Any:
        if value is STRAWBERRY_DEFAULT_VALUE:
            return Undefined
        else:
            return value

    def to_enum(self, enum: StrawberryEnum) -> GraphQLEnumType:

        values = ...

        graphql_enum = GraphQLEnumType(
            name=enum.name,
            values=values,
            description=enum.description,
            extensions=...,
            ast_node=...,
            extension_ast_nodes=...

        )

        return graphql_enum

    def to_interface(self, interface: StrawberryInterface) \
        -> GraphQLInterfaceType:

        graphql_fields = list(map(self.to_field, interface.fields))
        graphql_interfaces = list(map(self.to_interface, interface.interfaces))

        graphql_interface = GraphQLInterfaceType(
            name=interface.name,
            fields=graphql_fields,
            interfaces=graphql_interfaces,
            resolve_type=...,
            description=interface.description,
            extensions=...,
            ast_node=...,
            extension_ast_nodes=...
        )

        return graphql_interface

    def to_field(self, field: StrawberryField) -> GraphQLField:

        graphql_type = self.to_object_type(field.type)
        graphql_arguments = {
            argument.name: self.to_argument(argument)
            for argument in field.arguments
        }

        graphql_field = GraphQLField(
            type_=graphql_type,
            args=graphql_arguments,
            resolve=field.resolver,
            subscribe=...,
            description=field.description,
            deprecation_reason=...,
            extensions=...,
            ast_node=...
        )

        return graphql_field

    def to_object_type(self, object_type: StrawberryObjectType) \
        -> GraphQLObjectType:

        # Object has already been converted. Return it
        if object_type in self._type_map:
            return self._type_map[object_type]

        graphql_fields = list(map(self.to_field, object_type.fields))
        graphql_interfaces = list(
            map(self.to_interface, object_type.interfaces)
        )

        graphql_object_type = GraphQLObjectType(
            name=object_type.name,
            fields=graphql_fields,
            interfaces=graphql_interfaces
        )

        self._type_map[object_type] = graphql_object_type

        return graphql_object_type

    def to_schema(self, query: StrawberryObjectType,
                  mutation: Optional[StrawberryObjectType] = None,
                  subscription: Optional[StrawberryObjectType] = None) \
        -> GraphQLSchema:
        graphql_query = self.to_object_type(query)
        graphql_mutation = self.to_object_type(mutation) if mutation else None
        graphql_subscription = self.to_object_type(subscription) \
            if subscription else None

        schema = GraphQLSchema(
            query=graphql_query,
            mutation=graphql_mutation,
            subscription=graphql_subscription,
            directives=...,
            types=...
        )

        return schema
