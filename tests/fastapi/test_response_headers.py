from starlette.testclient import TestClient

import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from strawberry.types import Info


def test_set_response_headers():
    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self, info: Info) -> str:
            assert info.context.get("response") is not None
            info.context["response"].headers["X-Strawberry"] = "rocks"
            return "abc"

    app = FastAPI()
    schema = strawberry.Schema(query=Query)
    graphql_app = GraphQLRouter(schema)
    app.include_router(graphql_app, prefix="/graphql")

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}

    assert response.headers["x-strawberry"] == "rocks"


def test_set_cookie_headers():
    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self, info: Info) -> str:
            assert info.context.get("response") is not None
            info.context["response"].set_cookie(
                key="strawberry",
                value="rocks",
            )
            info.context["response"].set_cookie(
                key="FastAPI",
                value="rocks",
            )
            return "abc"

    app = FastAPI()
    schema = strawberry.Schema(query=Query)
    graphql_app = GraphQLRouter(schema)
    app.include_router(graphql_app, prefix="/graphql")

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}

    assert (
        response.headers["set-cookie"]
        == "strawberry=rocks; Path=/; SameSite=lax, FastAPI=rocks; Path=/; SameSite=lax"
    )
