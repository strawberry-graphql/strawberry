import json

import pytest

import strawberry
from flask import Flask
from strawberry.flask.views import GraphQLView


def create_app(**kwargs):
    @strawberry.type
    class Query:
        hello: str = "strawberry"

    schema = strawberry.Schema(query=Query)

    app = Flask(__name__)
    app.debug = True

    app.add_url_rule(
        "/graphql",
        view_func=GraphQLView.as_view(
            "graphql_view", schema=schema, root_value=Query(), **kwargs
        ),
    )
    return app


# @pytest.fixture
# def app(schema):
#     app = create_app(schema)

#     return app


@pytest.yield_fixture
def flask_client():
    app = create_app()

    with app.test_client() as client:
        yield client


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
