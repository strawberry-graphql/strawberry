import sys

import pytest

import strawberry
from sanic import Sanic
from strawberry.sanic.views import GraphQLView as BaseGraphQLView
from strawberry.types import ExecutionResult, Info

from .app import create_app


pytestmark = pytest.mark.skipif(
    sys.platform == "win32" and sys.version_info < (3, 8),
    reason="sanic doesn't seem to be working on windows with python < 3.8",
)


def test_graphql_query(sanic_client):
    query = {
        "query": """
            query {
                hello
            }
        """
    }

    request, response = sanic_client.test_client.post("/graphql", json=query)
    data = response.json
    assert response.status == 200
    assert data["data"]["hello"] == "strawberry"


def test_graphiql_view(sanic_client):
    request, response = sanic_client.test_client.get("/graphql")
    body = response.body.decode()

    assert "GraphiQL" in body


def test_graphiql_disabled_view():
    app = create_app(graphiql=False)

    request, response = app.test_client.get("/graphql")
    assert response.status == 404


def test_custom_context():
    class CustomGraphQLView(BaseGraphQLView):
        async def get_context(self, request):
            return {"request": request, "custom_value": "Hi!"}

    @strawberry.type
    class Query:
        @strawberry.field
        def custom_context_value(self, info: Info) -> str:
            return info.context["custom_value"]

    schema = strawberry.Schema(query=Query)

    app = Sanic("test-app-custom_context")
    app.debug = True

    app.add_route(CustomGraphQLView.as_view(schema=schema, graphiql=True), "/graphql")

    query = "{ customContextValue }"

    request, response = app.test_client.post("/graphql", json={"query": query})
    data = response.json

    assert response.status == 200
    assert data["data"] == {"customContextValue": "Hi!"}


def test_custom_process_result():
    class CustomGraphQLView(BaseGraphQLView):
        def process_result(self, result: ExecutionResult):
            return {}

    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self) -> str:
            return "ABC"

    schema = strawberry.Schema(query=Query)

    app = Sanic("test-app-custom_process_result")
    app.debug = True

    app.add_route(CustomGraphQLView.as_view(schema=schema, graphiql=True), "/graphql")

    query = "{ abc }"

    request, response = app.test_client.post("/graphql", json={"query": query})
    data = response.json

    assert response.status == 200
    assert data == {}


def test_malformed_query(sanic_client):
    query = {
        "qwary": """
            qwary {
                hello
            }
        """
    }

    request, response = sanic_client.test_client.post("/graphql", json=query)
    assert response.status == 400
