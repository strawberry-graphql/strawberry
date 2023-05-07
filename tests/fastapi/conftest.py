import pytest

from fastapi.testclient import TestClient
from tests.fastapi.app import create_app


@pytest.fixture
def test_client() -> TestClient:
    app = create_app()
    return TestClient(app)


@pytest.fixture
def test_client_keep_alive() -> TestClient:
    app = create_app(keep_alive=True, keep_alive_interval=0.1)
    return TestClient(app)


@pytest.fixture
def test_client_no_graphiql() -> TestClient:
    app = create_app(graphiql=False)
    return TestClient(app)
