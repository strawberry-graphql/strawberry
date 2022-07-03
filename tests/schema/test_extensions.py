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


DEFINITION_BACKREF = GraphQLCoreConverter.DEFINITION_BACKREF


def test_extensions_schema_directive():
    @strawberry.schema_directive(locations=[Location.OBJECT, Location.INPUT_OBJECT])
    class SchemaDirective:
        name: str

    @strawberry.type(directives=[SchemaDirective(name="Query")])
    class Query:
        hello: str

    schema = strawberry.Schema(query=Query)
    graphql_schema: GraphQLSchema = schema._schema

    # Schema
    assert graphql_schema.extensions[DEFINITION_BACKREF] is schema

    """
    FIXME: Apparently I stumbled on a bug:
           SchemaDirective are used on schema.__str__(),
           but aren't added to graphql_schema.directives

    graphql_scheme_directive = graphql_schema.get_directive("schemaDirective")
    """
    graphql_scheme_directive = schema.schema_converter.from_schema_directive(
        Query._type_definition.directives[0]
    )
    assert (
        graphql_scheme_directive.extensions[DEFINITION_BACKREF]
        is SchemaDirective.__strawberry_directive__
    )


def test_directive():
    @strawberry.directive(locations=[DirectiveLocation.FIELD])
    def uppercase(value: str, foo: str):
        return value.upper()

    @strawberry.type()
    class Query:
        hello: str

    schema = strawberry.Schema(query=Query, directives=[uppercase])
    graphql_schema: GraphQLSchema = schema._schema

    graphql_directive = graphql_schema.get_directive("uppercase")
    assert graphql_directive.extensions[DEFINITION_BACKREF] is uppercase
    assert (
        graphql_directive.args["foo"].extensions[DEFINITION_BACKREF]
        is uppercase.arguments[0]
    )


def test_enum():
    @strawberry.enum
    class ThingType(Enum):
        JSON = auto()
        STR = auto()

    @strawberry.type()
    class Query:
        hello: ThingType

    schema = strawberry.Schema(query=Query)
    graphql_schema: GraphQLSchema = schema._schema

    graphql_thing_type = cast(GraphQLEnumType, graphql_schema.get_type("ThingType"))
    assert (
        graphql_thing_type.extensions[DEFINITION_BACKREF] is ThingType._enum_definition
    )
    assert (
        graphql_thing_type.values["JSON"].extensions[DEFINITION_BACKREF]
        is ThingType._enum_definition.values[0]
    )
    assert (
        graphql_thing_type.values["STR"].extensions[DEFINITION_BACKREF]
        is ThingType._enum_definition.values[1]
    )


def test_scalar():
    @strawberry.type()
    class Query:
        hello: JSON
        hi: str

    schema = strawberry.Schema(query=Query)
    graphql_schema: GraphQLSchema = schema._schema

    assert (
        graphql_schema.get_type("JSON").extensions[DEFINITION_BACKREF]
        is JSON._scalar_definition
    )


def test_interface():
    @strawberry.interface
    class Thing:
        name: str

    @strawberry.type()
    class Query:
        hello: Thing

    schema = strawberry.Schema(query=Query)
    graphql_schema: GraphQLSchema = schema._schema

    assert (
        graphql_schema.get_type("Thing").extensions[DEFINITION_BACKREF]
        is Thing._type_definition
    )


def test_union():
    @strawberry.type
    class JsonThing:
        value: JSON

    @strawberry.type
    class StrThing:
        value: str

    SomeThing = strawberry.union("SomeThing", types=[JsonThing, StrThing])

    @strawberry.type()
    class Query:
        hello: SomeThing

    schema = strawberry.Schema(query=Query)
    graphql_schema: GraphQLSchema = schema._schema

    assert (
        graphql_schema.get_type("SomeThing").extensions[DEFINITION_BACKREF] is SomeThing
    )


def test_object_types():
    @strawberry.input
    class Input:
        name: str

    @strawberry.type()
    class Query:
        @strawberry.field
        def hello(self, input: Input) -> str:
            ...

    schema = strawberry.Schema(query=Query)
    graphql_schema: GraphQLSchema = schema._schema

    assert (
        graphql_schema.get_type("Input").extensions[DEFINITION_BACKREF]
        is Input._type_definition
    )
    assert (
        graphql_schema.get_type("Query").extensions[DEFINITION_BACKREF]
        is Query._type_definition
    )

    graphql_query = cast(GraphQLObjectType, graphql_schema.get_type("Query"))
    assert graphql_query.fields["hello"].extensions[
        DEFINITION_BACKREF
    ] is Query._type_definition.get_field("hello")
    assert (
        graphql_query.fields["hello"].args["input"].extensions[DEFINITION_BACKREF]
        is Query._type_definition.get_field("hello").arguments[0]
    )

    graphql_input = cast(GraphQLInputType, graphql_schema.get_type("Input"))
    assert graphql_input.fields["name"].extensions[
        DEFINITION_BACKREF
    ] is Input._type_definition.get_field("name")
