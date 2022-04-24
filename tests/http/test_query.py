import json

import pytest

from .clients import HttpClient


@pytest.mark.asyncio
async def test_graphql_query(http_client: HttpClient):
    response = await http_client.query(
        query="{ hello }",
        headers={
            "Content-Type": "application/json",
        },
    )
    data = json.loads(response.data.decode())

    assert response.status_code == 200
    assert data["data"]["hello"] == "Hello world"
