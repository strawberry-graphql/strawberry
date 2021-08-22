import pytest
from fastapi.testclient import TestClient

from tests.asgi.test_async import async_schema
from tests.fastapi.conftest import construct_app


@pytest.fixture
def test_client(async_schema):
    app = construct_app(async_schema)
    return TestClient(app)


def test_simple_query(schema, test_client):
    response = test_client.post("/graphql", json={"query": "{ hello }"})

    assert response.json() == {"data": {"hello": "Hello world"}}
