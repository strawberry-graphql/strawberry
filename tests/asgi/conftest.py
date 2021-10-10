import pytest

from starlette.testclient import TestClient

from strawberry.asgi.test import GraphQLTestClient
from tests.asgi.app import create_app


@pytest.fixture
def test_client():
    app = create_app()
    return TestClient(app)


@pytest.fixture
def test_client_keep_alive():
    app = create_app(keep_alive=True, keep_alive_interval=0.1)
    return TestClient(app)


@pytest.fixture
def test_client_no_graphiql():
    app = create_app(graphiql=False)
    return TestClient(app)


@pytest.fixture
def graphql_client(test_client):
    yield GraphQLTestClient(test_client)
