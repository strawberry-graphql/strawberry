from strawberry.http.async_base_view import AsyncBaseHTTPView
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL
from strawberry.subscriptions.protocols.graphql_transport_ws.types import (
    ConnectionAckMessage,
)
from tests.http.clients.base import HttpClient


async def test_turning_off_graphql_ws(http_client_class: type[HttpClient]):
    http_client = http_client_class()
    http_client.create_app(subscription_protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL])

    async with http_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_WS_PROTOCOL]
    ) as ws:
        await ws.receive(timeout=2)
        assert ws.closed
        assert ws.close_code == 4406
        assert ws.close_reason == "Subprotocol not acceptable"


async def test_turning_off_graphql_transport_ws(http_client_class: type[HttpClient]):
    http_client = http_client_class()
    http_client.create_app(subscription_protocols=[GRAPHQL_WS_PROTOCOL])

    async with http_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.receive(timeout=2)
        assert ws.closed
        assert ws.close_code == 4406
        assert ws.close_reason == "Subprotocol not acceptable"


async def test_turning_off_all_subprotocols(http_client_class: type[HttpClient]):
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


async def test_clients_can_prefer_subprotocols(http_client_class: type[HttpClient]):
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
    http_client: HttpClient, mocker
):
    spy = mocker.spy(AsyncBaseHTTPView, "encode_json")

    async with http_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.send_json({"type": "connection_init"})
        connection_ack_message: ConnectionAckMessage = await ws.receive_json()
        assert connection_ack_message == {"type": "connection_ack"}

        await ws.close()
        assert ws.closed

    assert spy.call_count == 1


async def test_handlers_use_the_views_decode_json_method(
    http_client: HttpClient, mocker
):
    spy = mocker.spy(AsyncBaseHTTPView, "decode_json")

    async with http_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.send_message({"type": "connection_init"})

        connection_ack_message: ConnectionAckMessage = await ws.receive_json()
        assert connection_ack_message == {"type": "connection_ack"}

        await ws.close()
        assert ws.closed

    assert spy.call_count == 1
