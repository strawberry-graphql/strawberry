import pytest
from graphql import (
    GraphQLField,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
)
from graphql import print_schema as graphql_core_print_schema

import strawberry


def test_generates_schema():
    @strawberry.type
    class Query:
        example: str

    schema = strawberry.Schema(query=Query)

    target_schema = GraphQLSchema(
        query=GraphQLObjectType(
            name="Query",
            fields={
                "example": GraphQLField(
                    GraphQLNonNull(GraphQLString), resolve=lambda obj, info: "world"
                )
            },
        )
    )

    assert schema.as_str().strip() == graphql_core_print_schema(target_schema).strip()


def test_schema_introspect_returns_the_introspection_query_result():
    @strawberry.type
    class Query:
        example: str

    schema = strawberry.Schema(query=Query)
    introspection = schema.introspect()
    assert {"__schema"} == introspection.keys()
    assert {
        "queryType",
        "mutationType",
        "subscriptionType",
        "types",
        "directives",
    } == introspection["__schema"].keys()


def test_schema_fails_on_an_invalid_schema():
    @strawberry.type
    class Query: ...  # Type must have at least one field

    with pytest.raises(ValueError, match="Invalid Schema. Errors.*"):
        strawberry.Schema(query=Query)
