import strawberry

from graphql import graphql_sync


def test_simple_type():
    @strawberry.type
    class Query:
        hello: str = "strawberry"

    schema = strawberry.Schema(query=Query)

    query = "{ hello }"

    result = graphql_sync(schema, query)

    assert result.data["hello"] == "strawberry"


def test_resolver():
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, root, info) -> str:
            return "I'm a resolver"

    assert Query().hello(None, None) == "I'm a resolver"

    schema = strawberry.Schema(query=Query)

    query = "{ hello }"

    result = graphql_sync(schema, query)

    assert result.data["hello"] == "I'm a resolver"
