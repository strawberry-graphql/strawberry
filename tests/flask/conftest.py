import pytest

from flask import Flask
from strawberry.flask.views import GraphQLView


def create_app(schema, **kwargs):
    app = Flask(__name__)
    app.debug = True
    app.add_url_rule(
        "/graphql",
        view_func=GraphQLView.as_view("graphql_view", schema=schema, **kwargs),
    )
    return app


@pytest.fixture
def app(schema):
    app = create_app(schema)
    ctx = app.app_context()
    ctx.push()
    return app


@pytest.yield_fixture
def flask_client(app):
    with app.test_client() as client:
        yield client
