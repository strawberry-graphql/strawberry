from typing import Literal

import pytest

from strawberry.http.base import BaseView

from .clients.base import HttpClient


@pytest.mark.parametrize("method", ["delete", "head", "put", "patch"])
async def test_does_only_allow_get_and_post(
    method: Literal["delete", "head", "put", "patch"],
    http_client: HttpClient,
):
    response = await http_client.request(url="/graphql", method=method)

    assert response.status_code == 405


async def test_the_http_handler_uses_the_views_decode_json_method(
    http_client: HttpClient, mocker
):
    spy = mocker.spy(BaseView, "decode_json")

    response = await http_client.query(query="{ hello }")
    assert response.status_code == 200
    assert response.headers["content-type"].split(";")[0] == "application/json"

    data = response.json["data"]
    assert isinstance(data, dict)
    assert data["hello"] == "Hello world"

    assert spy.call_count == 1


async def test_exception(http_client: HttpClient, mocker):
    response = await http_client.query(query="{ hello }", operation_name="wrong")
    assert response.status_code == 400
    assert response.headers["content-type"].split(";")[0] == "text/plain"
    assert response.data == b'Unknown operation named "wrong".'
