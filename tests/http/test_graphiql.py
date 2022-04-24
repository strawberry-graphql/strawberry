from typing import Type

import pytest

from .clients import HttpClient


@pytest.mark.parametrize("header_value", ["text/html", "*/*"])
async def test_renders_graphiql(header_value: str, http_client_class: Type[HttpClient]):
    http_client = http_client_class()
    response = await http_client.get("/graphql", headers={"Accept": header_value})

    assert response.status_code == 200

    assert "<title>Strawberry GraphiQL</title>" in response.text


async def test_does_not_render_graphiql_if_missing_accept(
    http_client_class: Type[HttpClient],
):
    http_client = http_client_class()
    response = await http_client.get("/graphql", headers={"Accept": "text/xml"})

    # TODO: django returns a 400, but we should be returning a 404
    assert response.status_code in (404, 400)


async def test_renders_graphiql_disabled(http_client_class: Type[HttpClient]):
    http_client = http_client_class(graphiql=False)
    response = await http_client.get("/graphql", headers={"Accept": "text/html"})

    assert response.status_code == 404
