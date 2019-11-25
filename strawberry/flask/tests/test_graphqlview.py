import json

import pytest

from flask import url_for

from .app import init_app


@pytest.fixture
def app():
    return init_app()


def test_graphql_query(client):
    query = {"query": "query {\n  user {\n    name\n    age\n  }\n}"}

    response = client.get(url_for("graphql_view"), json=query)
    data = json.loads(response.data.decode())

    assert response.status_code == 200
    assert data["data"]["user"]["name"] == "Patrick"
    assert data["data"]["user"]["age"] == 100


def test_playground_view(client):
    client.environ_base["HTTP_ACCEPT"] = "text/html"
    response = client.get(url_for("graphql_view"))
    body = response.data.decode()
    url = url_for("graphql_view") + "?"

    assert "GraphQL Playground" in body
    assert f'endpoint: "{url}"' in body
