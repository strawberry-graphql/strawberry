import json
from typing import Any

import strawberry
from sanic import Sanic
from strawberry.sanic.views import GraphQLView as BaseGraphQLView
from strawberry.types import ExecutionResult, Info

from .app import create_app


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
    assert data["data"]["hello"] == "Hello world"


def test_can_pass_variables(sanic_client):
    query = {
        "query": "query Hello($name: String!) { hello(name: $name) }",
        "variables": {"name": "James"},
    }

    request, response = sanic_client.test_client.post("/graphql", json=query)
    data = response.json
    assert response.status == 200
    assert data["data"]["hello"] == "Hello James"


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


def test_json_encoder():
    class CustomEncoder(json.JSONEncoder):
        def encode(self, o: Any) -> str:
            # Reverse the result.
            return super().encode(o)[::-1]

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, info: Info) -> str:
            return "strawberry"

    schema = strawberry.Schema(query=Query)

    app = Sanic("test-app-custom_context")
    app.debug = True

    app.add_route(
        BaseGraphQLView.as_view(
            schema=schema, graphiql=True, json_encoder=CustomEncoder
        ),
        "/graphql",
    )

    query = "{ hello }"

    request, response = app.test_client.post("/graphql", json={"query": query})
    data = response.content.decode()

    assert response.status == 200
    assert data[::-1] == '{"data": {"hello": "strawberry"}}'
