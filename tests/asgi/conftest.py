import pathlib

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
def test_client_no_get():
    app = create_app(allow_queries_via_get=False)
    return TestClient(app)


@pytest.fixture
def graphql_client(test_client):
    yield GraphQLTestClient(test_client)


def pytest_collection_modifyitems(config, items):
    # automatically mark tests with 'starlette' if they are in the asgi subfolder

    rootdir = pathlib.Path(config.rootdir)

    for item in items:
        rel_path = pathlib.Path(item.fspath).relative_to(rootdir)

        if str(rel_path).startswith("tests/asgi"):
            item.add_marker(pytest.mark.starlette)
