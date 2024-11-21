from typing import Type

from strawberry.http.async_base_view import AsyncBaseHTTPView
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL
from tests.http.clients.base import HttpClient


async def test_turning_off_graphql_ws(http_client_class: Type[HttpClient]):
    http_client = http_client_class()
    http_client.create_app(subscription_protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL])

    async with http_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_WS_PROTOCOL]
    ) as ws:
        await ws.receive(timeout=2)
        assert ws.closed
        assert ws.close_code == 4406
        assert ws.close_reason == "Subprotocol not acceptable"


async def test_turning_off_graphql_transport_ws(http_client_class: Type[HttpClient]):
    http_client = http_client_class()
    http_client.create_app(subscription_protocols=[GRAPHQL_WS_PROTOCOL])

    async with http_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.receive(timeout=2)
        assert ws.closed
        assert ws.close_code == 4406
        assert ws.close_reason == "Subprotocol not acceptable"


async def test_turning_off_all_subprotocols(http_client_class: Type[HttpClient]):
    http_client = http_client_class()
    http_client.create_app(subscription_protocols=[])

    async with http_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.receive(timeout=2)
        assert ws.closed
        assert ws.close_code == 4406
        assert ws.close_reason == "Subprotocol not acceptable"

    async with http_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_WS_PROTOCOL]
    ) as ws:
        await ws.receive(timeout=2)
        assert ws.closed
        assert ws.close_code == 4406
        assert ws.close_reason == "Subprotocol not acceptable"


async def test_generally_unsupported_subprotocols_are_rejected(http_client: HttpClient):
    async with http_client.ws_connect(
        "/graphql", protocols=["imaginary-protocol"]
    ) as ws:
        await ws.receive(timeout=2)
        assert ws.closed
        assert ws.close_code == 4406
        assert ws.close_reason == "Subprotocol not acceptable"


async def test_clients_can_prefer_subprotocols(http_client_class: Type[HttpClient]):
    http_client = http_client_class()
    http_client.create_app(
        subscription_protocols=[GRAPHQL_WS_PROTOCOL, GRAPHQL_TRANSPORT_WS_PROTOCOL]
    )

    async with http_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL]
    ) as ws:
        assert ws.accepted_subprotocol == GRAPHQL_TRANSPORT_WS_PROTOCOL
        await ws.close()
        assert ws.closed

    async with http_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_WS_PROTOCOL, GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        assert ws.accepted_subprotocol == GRAPHQL_WS_PROTOCOL
        await ws.close()
        assert ws.closed


async def test_handlers_use_the_views_encode_json_method(
    http_client: HttpClient, monkeypatch
):
    def mock_encode_json(self, data):
        return '{"custom": "json"}'

    monkeypatch.setattr(AsyncBaseHTTPView, "encode_json", mock_encode_json)

    async with http_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.send_json({"type": "connection_init"})
        message = await ws.receive_json()
        assert message == {"custom": "json"}

        await ws.close()
        assert ws.closed
