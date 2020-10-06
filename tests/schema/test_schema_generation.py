from graphql import (
    GraphQLField,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
    print_schema as graphql_core_print_schema,
)

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
