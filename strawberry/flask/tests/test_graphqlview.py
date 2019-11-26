import json

import pytest

import strawberry
from flask import Flask, url_for
from strawberry.flask.views import GraphQLView


@strawberry.type
class User:
    name: str
    age: int


@strawberry.type
class Query:
    @strawberry.field
    def user(self, info) -> User:
        return User(name="Patrick", age=100)


schema = strawberry.Schema(query=Query)


def init_app():
    app = Flask(__name__)
    app.debug = True
    app.add_url_rule(
        "/graphql", view_func=GraphQLView.as_view("graphql_view", schema=schema)
    )
    return app


if __name__ == "__main__":
    test_app = init_app()
    test_app.run()


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
