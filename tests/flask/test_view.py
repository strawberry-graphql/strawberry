import json

import strawberry
from flask import Flask, request
from strawberry.flask.views import GraphQLView as BaseGraphQLView
from strawberry.types import ExecutionResult, Info

from .app import create_app


def test_graphql_query(flask_client):
    query = {
        "query": """
            query {
                hello
            }
        """
    }

    response = flask_client.get("/graphql", json=query)
    data = json.loads(response.data.decode())

    assert response.status_code == 200
    assert data["data"]["hello"] == "strawberry"


def test_fails_when_request_body_has_invalid_json(flask_client):
    response = flask_client.post(
        "/graphql",
        data='{"qeury": "{__typena"',
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 400


def test_graphiql_view(flask_client):
    flask_client.environ_base["HTTP_ACCEPT"] = "text/html"
    response = flask_client.get("/graphql")
    body = response.data.decode()

    assert "GraphiQL" in body


def test_graphiql_disabled_view():
    app = create_app(graphiql=False)

    with app.test_client() as client:
        client.environ_base["HTTP_ACCEPT"] = "text/html"
        response = client.get("/graphql")

        assert response.status_code == 404


def test_custom_context():
    class CustomGraphQLView(BaseGraphQLView):
        def get_context(self):
            return {
                "request": request,
                "custom_value": "Hi!",
            }

    @strawberry.type
    class Query:
        @strawberry.field
        def custom_context_value(self, info: Info) -> str:
            return info.context["custom_value"]

    schema = strawberry.Schema(query=Query)

    app = Flask(__name__)
    app.debug = True

    app.add_url_rule(
        "/graphql",
        view_func=CustomGraphQLView.as_view("graphql_view", schema=schema),
    )

    with app.test_client() as client:
        query = "{ customContextValue }"

        response = client.get("/graphql", json={"query": query})
        data = json.loads(response.data.decode())

        assert response.status_code == 200
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

    app = Flask(__name__)
    app.debug = True

    app.add_url_rule(
        "/graphql",
        view_func=CustomGraphQLView.as_view("graphql_view", schema=schema),
    )

    with app.test_client() as client:
        query = "{ abc }"

        response = client.get("/graphql", json={"query": query})
        data = json.loads(response.data.decode())

        assert response.status_code == 200
        assert data == {}
