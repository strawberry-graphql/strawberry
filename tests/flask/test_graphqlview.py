import json

import pytest

import strawberry
from flask import url_for

from .conftest import create_app


@strawberry.type
class Query:
    hello: str = "strawberry"


schema = strawberry.Schema(query=Query)


def test_graphql_query(flask_client):
    query = {
        "query": """
            query {
                user {
                    name
                    age
                }
            }
        """
    }

    response = flask_client.get(url_for("graphql_view"), json=query)
    data = json.loads(response.data.decode())

    assert response.status_code == 200
    assert data["data"]["user"]["name"] == "Patrick"
    assert data["data"]["user"]["age"] == 100


def test_graphiql_view(flask_client):
    flask_client.environ_base["HTTP_ACCEPT"] = "text/html"
    response = flask_client.get(url_for("graphql_view"))
    body = response.data.decode()

    assert "GraphiQL" in body


@pytest.mark.parametrize("app", [create_app(schema=schema, graphiql=False)])
def test_graphiql_disabled_view(app, flask_client):
    flask_client.environ_base["HTTP_ACCEPT"] = "text/html"
    response = flask_client.get(url_for("graphql_view"))

    assert response.status_code == 404
