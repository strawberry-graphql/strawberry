from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import pytest

import strawberry

if TYPE_CHECKING:
    from starlette.testclient import TestClient


@pytest.fixture
def test_client() -> TestClient:
    from starlette.testclient import TestClient

    from strawberry.asgi import GraphQL

    @strawberry.type
    class Query:
        @strawberry.field
        async def hello(self, name: Optional[str] = None) -> str:
            return f"Hello {name or 'world'}"

    async_schema = strawberry.Schema(Query)
    app = GraphQL[None, None](async_schema)
    return TestClient(app)


def test_simple_query(test_client: TestClient):
    response = test_client.post("/", json={"query": "{ hello }"})

    assert response.json() == {"data": {"hello": "Hello world"}}
