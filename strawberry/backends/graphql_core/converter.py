from typing import Dict, Optional

from graphql import GraphQLArgument, GraphQLEnumType, GraphQLField, \
    GraphQLInterfaceType, GraphQLObjectType, GraphQLSchema, GraphQLType

from strawberry.types import StrawberryArgument, StrawberryEnum, \
    StrawberryField, StrawberryInterface, StrawberryObject, StrawberryObjectType


class GraphQLCoreConverter:

    def __init__(self):
        self._type_map: Dict[StrawberryObject, GraphQLType] = {}

    def to_argument(self, argument: StrawberryArgument) -> GraphQLArgument:
        ...

    def to_enum(self, enum: StrawberryEnum) -> GraphQLEnumType:
        ...

    def to_interface(self, interface: StrawberryInterface) \
        -> GraphQLInterfaceType:
        ...

    def to_field(self, field: StrawberryField) -> GraphQLField:
        ...

    def to_object_type(self, object_type: StrawberryObjectType) \
        -> GraphQLObjectType:
        graphql_fields = list(map(self.to_field, object_type.fields))
        graphql_interfaces = list(
            map(self.to_interface, object_type.interfaces))

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
