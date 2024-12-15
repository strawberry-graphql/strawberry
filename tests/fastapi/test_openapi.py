import strawberry


@strawberry.type
class Query:
    abc: str


def test_enable_graphiql_view_and_allow_queries_via_get():
    from fastapi import FastAPI
    from strawberry.fastapi import GraphQLRouter

    app = FastAPI()
    schema = strawberry.Schema(query=Query)
    graphql_app = GraphQLRouter[None, None](schema)
    app.include_router(graphql_app, prefix="/graphql")

    assert "get" in app.openapi()["paths"]["/graphql"]
    assert "post" in app.openapi()["paths"]["/graphql"]


def test_disable_graphiql_view_and_allow_queries_via_get():
    from fastapi import FastAPI
    from strawberry.fastapi import GraphQLRouter

    app = FastAPI()
    schema = strawberry.Schema(query=Query)
    graphql_app = GraphQLRouter[None, None](
        schema, graphql_ide=None, allow_queries_via_get=False
    )
    app.include_router(graphql_app, prefix="/graphql")

    assert "get" not in app.openapi()["paths"]["/graphql"]
    assert "post" in app.openapi()["paths"]["/graphql"]


def test_graphql_router_with_tags():
    from fastapi import FastAPI
    from strawberry.fastapi import GraphQLRouter

    app = FastAPI()
    schema = strawberry.Schema(query=Query)
    graphql_app = GraphQLRouter[None, None](schema, tags=["abc"])
    app.include_router(graphql_app, prefix="/graphql")

    assert "abc" in app.openapi()["paths"]["/graphql"]["get"]["tags"]
    assert "abc" in app.openapi()["paths"]["/graphql"]["post"]["tags"]
