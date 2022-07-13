import json

import strawberry
from flask import Flask, Response, request
from strawberry.flask.views import GraphQLView as BaseGraphQLView
from strawberry.types import ExecutionResult, Info

from .app import create_app


def test_graphql_query(flask_client, async_flask_client):
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
    assert data["data"]["hello"] == "Hello world"

    response = async_flask_client.get("/graphql", json=query)
    data = json.loads(response.data.decode())

    assert response.status_code == 200
    assert data["data"]["hello"] == "Hello world"


def test_can_pass_variables(flask_client, async_flask_client):
    query = {
        "query": "query Hello($name: String!) { hello(name: $name) }",
        "variables": {"name": "James"},
    }

    response = flask_client.get("/graphql", json=query)
    data = json.loads(response.data.decode())

    assert response.status_code == 200
    assert data["data"]["hello"] == "Hello James"

    response = async_flask_client.get("/graphql", json=query)
    data = json.loads(response.data.decode())

    assert response.status_code == 200
    assert data["data"]["hello"] == "Hello James"


def test_fails_when_request_body_has_invalid_json(flask_client, async_flask_client):
    response = flask_client.post(
        "/graphql",
        data='{"qeury": "{__typena"',
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 400

    response = async_flask_client.post(
        "/graphql",
        data='{"qeury": "{__typena"',
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 400


def test_graphiql_view(flask_client, async_flask_client):
    flask_client.environ_base["HTTP_ACCEPT"] = "text/html"
    response = flask_client.get("/graphql")
    body = response.data.decode()

    assert "GraphiQL" in body

    async_flask_client.environ_base["HTTP_ACCEPT"] = "text/html"
    response = async_flask_client.get("/graphql")
    body = response.data.decode()

    assert "GraphiQL" in body


def test_graphiql_disabled_view():
    app = create_app(graphiql=False)

    with app.test_client() as client:
        client.environ_base["HTTP_ACCEPT"] = "text/html"
        response = client.get("/graphql")

        assert response.status_code == 415


def test_custom_context():
    class CustomGraphQLView(BaseGraphQLView):
        def get_context(self, response: Response):
            return {
                "request": request,
                "response": response,
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


def test_context_with_response():
    @strawberry.type
    class Query:
        @strawberry.field
        def response(self, info: Info) -> bool:
            response: Response = info.context["response"]
            response.status_code = 401

            return True

    schema = strawberry.Schema(query=Query)

    app = Flask(__name__)
    app.debug = True

    app.add_url_rule(
        "/graphql",
        view_func=BaseGraphQLView.as_view("graphql_view", schema=schema),
    )

    with app.test_client() as client:
        query = "{ response }"

        response = client.get("/graphql", json={"query": query})
        assert response.status_code == 401
