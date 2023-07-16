from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from starlette.testclient import TestClient

    from strawberry.asgi.test import GraphQLTestClient


@pytest.fixture
def test_client() -> TestClient:
    from starlette.testclient import TestClient

    from tests.asgi.app import create_app

    app = create_app()
    return TestClient(app)


@pytest.fixture
def test_client_keep_alive() -> TestClient:
    from starlette.testclient import TestClient

    from tests.asgi.app import create_app

    app = create_app(keep_alive=True, keep_alive_interval=0.1)
    return TestClient(app)


@pytest.fixture
def test_client_no_graphiql() -> TestClient:
    from starlette.testclient import TestClient

    from tests.asgi.app import create_app

    app = create_app(graphiql=False)
    return TestClient(app)


@pytest.fixture
def test_client_no_get() -> TestClient:
    from starlette.testclient import TestClient

    from tests.asgi.app import create_app

    app = create_app(allow_queries_via_get=False)
    return TestClient(app)


@pytest.fixture
def graphql_client(test_client: TestClient) -> GraphQLTestClient:
    from strawberry.asgi.test import GraphQLTestClient

    return GraphQLTestClient(test_client)
