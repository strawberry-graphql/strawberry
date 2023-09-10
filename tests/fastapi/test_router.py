import pytest

import strawberry


def test_include_router_prefix():
    from starlette.testclient import TestClient

    from fastapi import FastAPI
    from strawberry.fastapi import GraphQLRouter

    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self) -> str:
            return "abc"

    app = FastAPI()
    schema = strawberry.Schema(query=Query)
    graphql_app = GraphQLRouter[None, None](schema)
    app.include_router(graphql_app, prefix="/graphql")

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}


def test_graphql_router_path():
    from starlette.testclient import TestClient

    from fastapi import FastAPI
    from strawberry.fastapi import GraphQLRouter

    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self) -> str:
            return "abc"

    app = FastAPI()
    schema = strawberry.Schema(query=Query)
    graphql_app = GraphQLRouter[None, None](schema, path="/graphql")
    app.include_router(graphql_app)

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}


def test_missing_path_and_prefix():
    from fastapi import FastAPI
    from strawberry.fastapi import GraphQLRouter

    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self) -> str:
            return "abc"

    app = FastAPI()
    schema = strawberry.Schema(query=Query)
    graphql_app = GraphQLRouter[None, None](schema)

    with pytest.raises(Exception) as exc:
        app.include_router(graphql_app)

    assert "Prefix and path cannot be both empty" in str(exc)
