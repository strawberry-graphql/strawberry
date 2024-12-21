from enum import Enum, auto
from typing import Annotated, Union, cast

from graphql import (
    DirectiveLocation,
    GraphQLEnumType,
    GraphQLInputType,
    GraphQLObjectType,
    GraphQLSchema,
)

import strawberry
from strawberry.directive import DirectiveValue
from strawberry.scalars import JSON
from strawberry.schema.schema_converter import GraphQLCoreConverter
from strawberry.schema_directive import Location
from strawberry.types.base import get_object_definition

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

    # TODO: Apparently I stumbled on a bug:
    #        SchemaDirective are used on schema.__str__(),
    #        but aren't added to graphql_schema.directives
    # maybe graphql_schema_directive = graphql_schema.get_directive("schemaDirective")

    directives = get_object_definition(Query, strict=True).directives
    assert directives is not None
    graphql_schema_directive = schema.schema_converter.from_schema_directive(
        directives[0]
    )
    assert (
        graphql_schema_directive.extensions[DEFINITION_BACKREF]
        is SchemaDirective.__strawberry_directive__
    )


def test_directive():
    @strawberry.directive(locations=[DirectiveLocation.FIELD])
    def uppercase(value: DirectiveValue[str], foo: str):  # pragma: no cover
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
        is Thing.__strawberry_definition__
    )


def test_union():
    @strawberry.type
    class JsonThing:
        value: JSON

    @strawberry.type
    class StrThing:
        value: str

    SomeThing = Annotated[Union[JsonThing, StrThing], strawberry.union("SomeThing")]

    @strawberry.type()
    class Query:
        hello: SomeThing

    schema = strawberry.Schema(query=Query)
    graphql_schema: GraphQLSchema = schema._schema
    graphql_type = graphql_schema.get_type("SomeThing")

    assert graphql_type.extensions[DEFINITION_BACKREF].graphql_name == "SomeThing"
    assert graphql_type.extensions[DEFINITION_BACKREF].description is None


def test_object_types():
    @strawberry.input
    class Input:
        name: str

    @strawberry.type()
    class Query:
        @strawberry.field
        def hello(self, input: Input) -> str: ...

    schema = strawberry.Schema(query=Query)
    graphql_schema: GraphQLSchema = schema._schema

    assert (
        graphql_schema.get_type("Input").extensions[DEFINITION_BACKREF]
        is Input.__strawberry_definition__
    )
    assert (
        graphql_schema.get_type("Query").extensions[DEFINITION_BACKREF]
        is Query.__strawberry_definition__
    )

    graphql_query = cast("GraphQLObjectType", graphql_schema.get_type("Query"))
    assert graphql_query.fields["hello"].extensions[
        DEFINITION_BACKREF
    ] is Query.__strawberry_definition__.get_field("hello")
    assert (
        graphql_query.fields["hello"].args["input"].extensions[DEFINITION_BACKREF]
        is Query.__strawberry_definition__.get_field("hello").arguments[0]
    )

    graphql_input = cast(GraphQLInputType, graphql_schema.get_type("Input"))
    assert graphql_input.fields["name"].extensions[
        DEFINITION_BACKREF
    ] is Input.__strawberry_definition__.get_field("name")
