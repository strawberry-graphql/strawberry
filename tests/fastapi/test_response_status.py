from starlette import status
from starlette.testclient import TestClient

import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from strawberry.types import Info


def test_set_custom_http_response_status():
    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self, info: Info) -> str:
            assert info.context.get("response") is not None
            info.context["response"].status_code = status.HTTP_418_IM_A_TEAPOT
            return "abc"

    app = FastAPI()
    schema = strawberry.Schema(query=Query)
    graphql_app = GraphQLRouter(schema)
    app.include_router(graphql_app, prefix="/graphql")

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 418
    assert response.json() == {"data": {"abc": "abc"}}


def test_set_without_setting_http_response_status():
    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self) -> str:
            return "abc"

    app = FastAPI()
    schema = strawberry.Schema(query=Query)
    graphql_app = GraphQLRouter(schema)
    app.include_router(graphql_app, prefix="/graphql")

    test_client = TestClient(app)
    response = test_client.post("/graphql", json={"query": "{ abc }"})

    assert response.status_code == 200
    assert response.json() == {"data": {"abc": "abc"}}
