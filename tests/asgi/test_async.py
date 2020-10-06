import typing

import pytest

from starlette.testclient import TestClient

import strawberry
from strawberry.asgi import GraphQL


@pytest.fixture
def async_schema():
    @strawberry.type
    class Query:
        @strawberry.field
        async def hello(self, info, name: typing.Optional[str] = None) -> str:
            return f"Hello {name or 'world'}"

    return strawberry.Schema(Query)


@pytest.fixture
def test_client(async_schema):
    app = GraphQL(async_schema)

    return TestClient(app)


def test_simple_query(schema, test_client):
    response = test_client.post("/", json={"query": "{ hello }"})

    assert response.json() == {"data": {"hello": "Hello world"}}
