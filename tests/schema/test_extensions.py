from enum import Enum, auto
from typing import cast

from graphql import (
    DirectiveLocation,
    GraphQLEnumType,
    GraphQLInputType,
    GraphQLObjectType,
    GraphQLSchema,
)

import strawberry
from strawberry.scalars import JSON
from strawberry.schema.schema_converter import STRAWBERRY_DEFINITION


def test_extensions():
    @strawberry.directive(locations=[DirectiveLocation.FIELD])
    def uppercase(value: str, foo: str):
        return value.upper()

    print("uppercase.args", uppercase.arguments[0])

    @strawberry.enum
    class ThingType(Enum):
        JSON = auto()
        STR = auto()

    @strawberry.input
    class Input:
        type: ThingType

    @strawberry.interface
    class Thing:
        name: str

    @strawberry.type
    class JsonThing(Thing):
        value: JSON

    @strawberry.type
    class StrThing(Thing):
        value: str

    SomeThing = strawberry.union("SomeThing", types=[JsonThing, StrThing])

    @strawberry.type
    class Query:
        @strawberry.field
        def get_thing_iface(input: Input) -> Thing:
            ...

        @strawberry.field
        def get_thing_union(input: Input) -> SomeThing:
            ...

    strawberry_schema = strawberry.Schema(query=Query, directives=[uppercase])
    graphql_schema: GraphQLSchema = strawberry_schema._schema
    print(strawberry_schema)

    # Schema
    assert graphql_schema.extensions[STRAWBERRY_DEFINITION] is strawberry_schema

    # Directive
    graphql_directive = graphql_schema.get_directive("uppercase")
    assert graphql_directive.extensions[STRAWBERRY_DEFINITION] is uppercase
    assert (
        graphql_directive.args["foo"].extensions[STRAWBERRY_DEFINITION]
        is uppercase.arguments[0]
    )

    # Leaf types: Enums and scalars
    assert (
        graphql_schema.get_type("JSON").extensions[STRAWBERRY_DEFINITION]
        is JSON._scalar_definition
    )
    graphql_thing_type = cast(GraphQLEnumType, graphql_schema.get_type("ThingType"))
    assert (
        graphql_thing_type.extensions[STRAWBERRY_DEFINITION]
        is ThingType._enum_definition
    )
    assert (
        graphql_thing_type.values["JSON"].extensions[STRAWBERRY_DEFINITION]
        is ThingType._enum_definition.values[0]
    )
    assert (
        graphql_thing_type.values["STR"].extensions[STRAWBERRY_DEFINITION]
        is ThingType._enum_definition.values[1]
    )

    # Abstract types: Interfaces and Unions
    assert (
        graphql_schema.get_type("Thing").extensions[STRAWBERRY_DEFINITION]
        is Thing._type_definition
    )
    assert (
        graphql_schema.get_type("SomeThing").extensions[STRAWBERRY_DEFINITION]
        is SomeThing
    )

    # Object types
    assert (
        graphql_schema.get_type("JsonThing").extensions[STRAWBERRY_DEFINITION]
        is JsonThing._type_definition
    )
    assert (
        graphql_schema.get_type("StrThing").extensions[STRAWBERRY_DEFINITION]
        is StrThing._type_definition
    )
    assert (
        graphql_schema.get_type("Input").extensions[STRAWBERRY_DEFINITION]
        is Input._type_definition
    )
    assert (
        graphql_schema.get_type("Query").extensions[STRAWBERRY_DEFINITION]
        is Query._type_definition
    )

    # Fields
    graphql_query = cast(GraphQLObjectType, graphql_schema.get_type("Query"))
    graphql_query.fields["getThingIface"].extensions[
        STRAWBERRY_DEFINITION
    ] is Query._type_definition.get_field("get_thing_iface")
    graphql_query.fields["getThingIface"].args[
        "input"
    ] is Query._type_definition.get_field("get_thing_iface").arguments[0]

    graphql_input = cast(GraphQLInputType, graphql_schema.get_type("Input"))
    graphql_input.fields["type"].extensions[
        STRAWBERRY_DEFINITION
    ] is Input._type_definition.get_field("type")
