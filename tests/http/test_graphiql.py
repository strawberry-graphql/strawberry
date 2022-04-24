from typing import Type

import pytest

from .clients import HttpClient


@pytest.mark.asyncio
async def test_renders_graphiql(http_client_class: Type[HttpClient]):
    http_client = http_client_class()
    response = await http_client.get("/graphql", headers={"Accept": "text/html"})

    assert response.status_code == 200

    assert "<title>Strawberry GraphiQL</title>" in response.text


@pytest.mark.asyncio
async def test_renders_graphiql_disabled(http_client_class: Type[HttpClient]):
    http_client = http_client_class(graphiql=False)
    response = await http_client.get("/graphql", headers={"Accept": "text/html"})

    assert response.status_code == 404
