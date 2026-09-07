import json
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


@pytest.mark.parametrize("as_bytes", [False, True])
async def test_the_http_handler_preserves_custom_encoded_json(
    http_client: HttpClient, mocker, request, as_bytes: bool
):
    if request.node.get_closest_marker("channels"):
        pytest.skip("Channels HTTP responses use a separate serialization path")

    def patched_encode_json(self, data: object) -> str | bytes:
        encoded = json.dumps(data, ensure_ascii=False, indent=2)
        return encoded.encode() if as_bytes else encoded

    mocker.patch("strawberry.http.base.BaseView.encode_json", patched_encode_json)
    if request.node.get_closest_marker("django"):
        mocker.patch(
            "strawberry.django.views.BaseView.encode_json", patched_encode_json
        )

    response = await http_client.query(query='{ hello(name: "café 🍓") }')
    assert response.status_code == 200
    assert response.headers["content-type"].split(";")[0] == "application/json"

    data = response.json["data"]
    assert isinstance(data, dict)
    assert data["hello"] == "Hello café 🍓"
    assert response.text == json.dumps(response.json, ensure_ascii=False, indent=2)


@pytest.mark.parametrize("query", ['{ hello(name: "café 🍓, :") }', "{ alwaysFail }"])
async def test_default_http_json_is_compact(http_client: HttpClient, request, query):
    if request.node.get_closest_marker("channels"):
        pytest.skip("Channels HTTP responses use a separate serialization path")

    response = await http_client.query(query=query)

    assert response.status_code == 200
    assert response.text == json.dumps(response.json, separators=(",", ":"))
    if "hello" in query:
        assert response.json["data"] == {"hello": "Hello café 🍓, :"}
        assert r"\u00e9 \ud83c\udf53" in response.text
    else:
        assert response.json["errors"]


async def test_exception(http_client: HttpClient, mocker):
    response = await http_client.query(query="{ hello }", operation_name="wrong")
    assert response.status_code == 400
    assert response.headers["content-type"].split(";")[0] == "text/plain"
    assert response.data == b'Unknown operation named "wrong".'
