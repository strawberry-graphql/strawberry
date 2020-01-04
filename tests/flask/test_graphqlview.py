import json

import pytest

from flask import Flask, url_for
from strawberry.flask.views import GraphQLView


def init_app(schema=None):
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
@pytest.mark.usefixtures("schema")
def app(schema):
    return init_app(schema)


def test_graphql_query(client):
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
