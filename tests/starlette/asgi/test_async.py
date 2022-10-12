import typing

import pytest

from starlette.testclient import TestClient

import strawberry
from strawberry.asgi import GraphQL


@pytest.fixture
def test_client():
    @strawberry.type
    class Query:
        @strawberry.field
        async def hello(self, name: typing.Optional[str] = None) -> str:
            return f"Hello {name or 'world'}"

    async_schema = strawberry.Schema(Query)
    app = GraphQL(async_schema)
    return TestClient(app)


def test_simple_query(test_client):
    response = test_client.post("/", json={"query": "{ hello }"})

    assert response.json() == {"data": {"hello": "Hello world"}}
