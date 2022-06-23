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
from strawberry.schema.schema_converter import GraphQLCoreConverter
from strawberry.schema_directive import Location


def test_extensions():
    @strawberry.schema_directive(locations=[Location.OBJECT, Location.INPUT_OBJECT])
    class SchemaDirective:
        name: str

    @strawberry.directive(locations=[DirectiveLocation.FIELD])
    def uppercase(value: str, foo: str):
        return value.upper()

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

    @strawberry.type(directives=[SchemaDirective(name="Query")])
    class Query:
        @strawberry.field
        def get_thing_iface(input: Input) -> Thing:
            ...

        @strawberry.field
        def get_thing_union(input: Input) -> SomeThing:
            ...

    strawberry_schema = strawberry.Schema(query=Query, directives=[uppercase])
    graphql_schema: GraphQLSchema = strawberry_schema._schema

    # Schema
    assert (
        graphql_schema.extensions[GraphQLCoreConverter.DEFINITION_BACKREF]
        is strawberry_schema
    )

    # SchemaDirective
    """
    FIXME: Apparently I stumpled on a bug:
           SchemaDirective are used on strawberry_schema.__str__(),
           but aren't added to graphql_schema.directives

    graphql_scheme_directive = graphql_schema.get_directive("schemaDirective")
    """
    graphql_scheme_directive = strawberry_schema.schema_converter.from_schema_directive(
        Query._type_definition.directives[0]
    )
    assert (
        graphql_scheme_directive.extensions[GraphQLCoreConverter.DEFINITION_BACKREF]
        is SchemaDirective.__strawberry_directive__
    )

    # Directive
    graphql_directive = graphql_schema.get_directive("uppercase")
    assert (
        graphql_directive.extensions[GraphQLCoreConverter.DEFINITION_BACKREF]
        is uppercase
    )
    assert (
        graphql_directive.args["foo"].extensions[
            GraphQLCoreConverter.DEFINITION_BACKREF
        ]
        is uppercase.arguments[0]
    )

    # Leaf types: Enums and scalars
    assert (
        graphql_schema.get_type("JSON").extensions[
            GraphQLCoreConverter.DEFINITION_BACKREF
        ]
        is JSON._scalar_definition
    )
    graphql_thing_type = cast(GraphQLEnumType, graphql_schema.get_type("ThingType"))
    assert (
        graphql_thing_type.extensions[GraphQLCoreConverter.DEFINITION_BACKREF]
        is ThingType._enum_definition
    )
    assert (
        graphql_thing_type.values["JSON"].extensions[
            GraphQLCoreConverter.DEFINITION_BACKREF
        ]
        is ThingType._enum_definition.values[0]
    )
    assert (
        graphql_thing_type.values["STR"].extensions[
            GraphQLCoreConverter.DEFINITION_BACKREF
        ]
        is ThingType._enum_definition.values[1]
    )

    # Abstract types: Interfaces and Unions
    assert (
        graphql_schema.get_type("Thing").extensions[
            GraphQLCoreConverter.DEFINITION_BACKREF
        ]
        is Thing._type_definition
    )
    assert (
        graphql_schema.get_type("SomeThing").extensions[
            GraphQLCoreConverter.DEFINITION_BACKREF
        ]
        is SomeThing
    )

    # Object types
    assert (
        graphql_schema.get_type("JsonThing").extensions[
            GraphQLCoreConverter.DEFINITION_BACKREF
        ]
        is JsonThing._type_definition
    )
    assert (
        graphql_schema.get_type("StrThing").extensions[
            GraphQLCoreConverter.DEFINITION_BACKREF
        ]
        is StrThing._type_definition
    )
    assert (
        graphql_schema.get_type("Input").extensions[
            GraphQLCoreConverter.DEFINITION_BACKREF
        ]
        is Input._type_definition
    )
    assert (
        graphql_schema.get_type("Query").extensions[
            GraphQLCoreConverter.DEFINITION_BACKREF
        ]
        is Query._type_definition
    )

    # Fields
    graphql_query = cast(GraphQLObjectType, graphql_schema.get_type("Query"))
    assert graphql_query.fields["getThingIface"].extensions[
        GraphQLCoreConverter.DEFINITION_BACKREF
    ] is Query._type_definition.get_field("get_thing_iface")
    assert (
        graphql_query.fields["getThingIface"]
        .args["input"]
        .extensions[GraphQLCoreConverter.DEFINITION_BACKREF]
        is Query._type_definition.get_field("get_thing_iface").arguments[0]
    )

    graphql_input = cast(GraphQLInputType, graphql_schema.get_type("Input"))
    assert graphql_input.fields["type"].extensions[
        GraphQLCoreConverter.DEFINITION_BACKREF
    ] is Input._type_definition.get_field("type")
