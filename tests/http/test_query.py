import json
from typing import Type

import pytest

from .clients import HttpClient


@pytest.mark.asyncio
async def test_graphql_query(http_client_class: Type[HttpClient]):
    http_client = http_client_class()

    query = {
        "query": """
            query {
                hello
            }
        """
    }

    response = await http_client.post("/graphql", json=query)
    data = json.loads(response.data.decode())

    assert response.status_code == 200
    assert data["data"]["hello"] == "Hello world"
