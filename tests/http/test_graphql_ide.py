from typing import Union
from typing_extensions import Literal

import pytest

from .clients.base import HttpClient


@pytest.mark.parametrize("header_value", ["text/html", "*/*"])
@pytest.mark.parametrize("graphql_ide", ["graphiql", "apollo-sandbox", "pathfinder"])
async def test_renders_graphql_ide(
    header_value: str,
    http_client_class: type[HttpClient],
    graphql_ide: Literal["graphiql", "apollo-sandbox", "pathfinder"],
):
    http_client = http_client_class(graphql_ide=graphql_ide)

    response = await http_client.get("/graphql", headers={"Accept": header_value})
    content_type = response.headers.get(
        "content-type", response.headers.get("Content-Type", "")
    )

    assert response.status_code == 200
    assert "text/html" in content_type
    assert "<title>Strawberry" in response.text

    if graphql_ide == "apollo-sandbox":
        assert "embeddable-sandbox.cdn.apollographql" in response.text

    if graphql_ide == "pathfinder":
        assert "@pathfinder-ide/react" in response.text

    if graphql_ide == "graphiql":
        assert "unpkg.com/graphiql" in response.text


@pytest.mark.parametrize("header_value", ["text/html", "*/*"])
async def test_renders_graphql_ide_deprecated(
    header_value: str, http_client_class: type[HttpClient]
):
    with pytest.deprecated_call(
        match=r"The `graphiql` argument is deprecated in favor of `graphql_ide`"
    ):
        http_client = http_client_class(graphiql=True)

        response = await http_client.get("/graphql", headers={"Accept": header_value})

    content_type = response.headers.get(
        "content-type", response.headers.get("Content-Type", "")
    )

    assert response.status_code == 200
    assert "text/html" in content_type
    assert "<title>Strawberry GraphiQL</title>" in response.text

    assert "https://unpkg.com/graphiql" in response.text


async def test_does_not_render_graphiql_if_wrong_accept(
    http_client_class: type[HttpClient],
):
    http_client = http_client_class()
    response = await http_client.get("/graphql", headers={"Accept": "text/xml"})

    # THIS might need to be changed to 404

    assert response.status_code == 400


@pytest.mark.parametrize("graphql_ide", [False, None])
async def test_renders_graphiql_disabled(
    http_client_class: type[HttpClient],
    graphql_ide: Union[bool, None],
):
    http_client = http_client_class(graphql_ide=graphql_ide)
    response = await http_client.get("/graphql", headers={"Accept": "text/html"})

    assert response.status_code == 404


async def test_renders_graphiql_disabled_deprecated(
    http_client_class: type[HttpClient],
):
    with pytest.deprecated_call(
        match=r"The `graphiql` argument is deprecated in favor of `graphql_ide`"
    ):
        http_client = http_client_class(graphiql=False)
        response = await http_client.get("/graphql", headers={"Accept": "text/html"})

    assert response.status_code == 404
