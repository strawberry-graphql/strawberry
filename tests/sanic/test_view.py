import json
from typing import Any

import strawberry
from sanic import Sanic
from strawberry.sanic.views import GraphQLView as BaseGraphQLView
from strawberry.types import ExecutionResult, Info


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
