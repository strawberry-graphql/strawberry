import pytest

from flask import Flask
from strawberry.flask.views import GraphQLView


@pytest.fixture
def app(schema):
    app = Flask(__name__)
    app.debug = True
    app.add_url_rule(
        "/graphql", view_func=GraphQLView.as_view("graphql_view", schema=schema)
    )
    return app


@pytest.yield_fixture
def flask_client(app):
    with app.test_client() as client:
        yield client
