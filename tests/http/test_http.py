import pytest

from strawberry.http.base import BaseView

from .clients.base import HttpClient


@pytest.mark.parametrize("method", ["delete", "head", "put", "patch"])
async def test_does_only_allow_get_and_post(
    method: str,
    http_client: HttpClient,
):
    response = await http_client.request(url="/graphql", method=method)  # type: ignore

    assert response.status_code == 405


async def test_the_http_handler_uses_the_views_decode_json_method(
    http_client: HttpClient, mocker
):
    spy = mocker.spy(BaseView, "decode_json")

    response = await http_client.query(query="{ hello }")
    assert response.status_code == 200

    data = response.json["data"]
    assert isinstance(data, dict)
    assert data["hello"] == "Hello world"

    assert spy.call_count == 1
