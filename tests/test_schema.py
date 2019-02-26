import strawberry

from graphql import graphql_sync


def test_simple_type():
    @strawberry.type
    class Query:
        hello: str = "strawberry"

    schema = strawberry.Schema(query=Query)

    query = "{ hello }"

    result = graphql_sync(schema, query)

    assert not result.errors
    assert result.data["hello"] == "strawberry"


def test_resolver():
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, info) -> str:
            return "I'm a resolver"

    assert Query().hello(None) == "I'm a resolver"

    schema = strawberry.Schema(query=Query)

    query = "{ hello }"

    result = graphql_sync(schema, query)

    assert not result.errors
    assert result.data["hello"] == "I'm a resolver"


def test_nested_types():
    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self, info) -> User:
            return User(name="Patrick")

    assert Query().user(None) == User(name="Patrick")

    schema = strawberry.Schema(query=Query)

    query = "{ user { name } }"

    result = graphql_sync(schema, query)

    assert not result.errors
    assert result.data["user"]["name"] == "Patrick"
