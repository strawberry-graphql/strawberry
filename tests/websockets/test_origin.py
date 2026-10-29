import logging

import pytest

from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL
from tests.http.clients.base import HttpClient, WebSocketRejectedError
from tests.views.schema import schema

API_HOST = "api.example.com"


async def assert_connects(http_client: HttpClient, headers: dict[str, str]) -> None:
    async with http_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL], headers=headers
    ) as ws:
        await ws.send_json({"type": "connection_init"})
        assert await ws.receive_json() == {"type": "connection_ack"}
        await ws.close()


async def assert_rejected(http_client: HttpClient, headers: dict[str, str]) -> None:
    with pytest.raises(WebSocketRejectedError):
        async with http_client.ws_connect(
            "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL], headers=headers
        ):
            pass  # pragma: no cover


async def test_allows_clients_without_origin(http_client: HttpClient):
    await assert_connects(http_client, headers={"host": API_HOST})


async def test_allows_same_origin(http_client: HttpClient):
    await assert_connects(
        http_client, headers={"host": API_HOST, "origin": f"https://{API_HOST}"}
    )


async def test_allows_same_origin_reported_by_fetch_metadata(http_client: HttpClient):
    # e.g. behind a proxy that rewrites the Host header
    await assert_connects(
        http_client,
        headers={
            "host": "127.0.0.1:8000",
            "origin": f"https://{API_HOST}",
            "sec-fetch-site": "same-origin",
        },
    )


async def test_rejects_cross_origin_by_default(
    http_client: HttpClient, caplog: pytest.LogCaptureFixture
):
    with caplog.at_level(logging.WARNING, logger="strawberry.ws"):
        await assert_rejected(
            http_client, headers={"host": API_HOST, "origin": "https://evil.example"}
        )

    assert caplog.messages == [
        (
            "Rejected WebSocket connection from origin 'https://evil.example' to "
            "host 'api.example.com'. If pages on this origin should be able to "
            "connect, add it to `allowed_origins`."
        )
    ]


async def test_rejects_sibling_origin_on_the_same_site(http_client: HttpClient):
    # SameSite=Lax cookies are sent from sibling subdomains and other ports
    await assert_rejected(
        http_client,
        headers={
            "host": API_HOST,
            "origin": "https://other.example.com",
            "sec-fetch-site": "same-site",
        },
    )


async def test_rejects_null_origin(http_client: HttpClient):
    await assert_rejected(http_client, headers={"host": API_HOST, "origin": "null"})


async def test_allowed_origins(http_client_class: type[HttpClient]):
    http_client = http_client_class(
        schema, allowed_origins=["https://App.example.com:443"]
    )

    await assert_connects(
        http_client, headers={"host": API_HOST, "origin": "https://app.example.com"}
    )
    await assert_rejected(
        http_client, headers={"host": API_HOST, "origin": "http://app.example.com"}
    )
    await assert_rejected(
        http_client, headers={"host": API_HOST, "origin": "https://evil.example"}
    )


async def test_allowed_origins_wildcard(http_client_class: type[HttpClient]):
    http_client = http_client_class(schema, allowed_origins=["*"])

    await assert_connects(
        http_client, headers={"host": API_HOST, "origin": "https://evil.example"}
    )
