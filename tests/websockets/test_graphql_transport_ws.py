import asyncio
import json
from datetime import timedelta
from typing import AsyncGenerator, Type

import pytest
import pytest_asyncio

from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL
from strawberry.subscriptions.protocols.graphql_transport_ws.types import (
    CompleteMessage,
    ConnectionAckMessage,
    ConnectionInitMessage,
    ErrorMessage,
    NextMessage,
    PingMessage,
    PongMessage,
    SubscribeMessage,
    SubscribeMessagePayload,
)
from tests.http.clients import AioHttpClient

from ..http.clients import HttpClient, WebSocketClient


@pytest_asyncio.fixture
async def ws_raw(http_client: HttpClient) -> AsyncGenerator[WebSocketClient, None]:
    async with http_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        yield ws


async def test_unknown_message_type(ws_raw: WebSocketClient):
    ws = ws_raw

    await ws.send_json({"type": "NOT_A_MESSAGE_TYPE"})

    data = await ws.receive(timeout=2)
    assert ws.closed
    assert ws.close_code == 4400
    ws.assert_reason("Unknown message type: NOT_A_MESSAGE_TYPE")


async def test_missing_message_type(ws_raw: WebSocketClient):
    ws = ws_raw

    await ws.send_json({"notType": None})

    data = await ws.receive(timeout=2)
    assert ws.closed
    assert ws.close_code == 4400
    ws.assert_reason("Failed to parse message")


async def test_parsing_an_invalid_message(ws_raw: WebSocketClient):
    ws = ws_raw

    await ws.send_json({"type": "subscribe", "notPayload": None})

    data = await ws.receive(timeout=2)
    assert ws.closed
    assert ws.close_code == 4400
    ws.assert_reason("Failed to parse message")


async def test_parsing_an_invalid_payload(ws_raw: WebSocketClient):
    ws = ws_raw

    await ws.send_json({"type": "subscribe", "payload": {"unexpectedField": 42}})

    data = await ws.receive(timeout=2)
    assert ws.closed
    assert ws.close_code == 4400
    ws.assert_reason("Failed to parse message")


async def test_ws_messages_must_be_text(ws_raw: WebSocketClient):
    ws = ws_raw

    await ws.send_bytes(json.dumps(ConnectionInitMessage().as_dict()).encode())

    data = await ws.receive(timeout=2)
    assert ws.closed
    assert ws.close_code == 4400
    ws.assert_reason("WebSocket message type must be text")


# @pytest.mark.xfail(
async def test_connection_init_timeout(request, http_client_class: Type[HttpClient]):
    if http_client_class == AioHttpClient:
        pytest.skip(
            "Closing a AIOHTTP WebSocket from a task currently doesnt work as expected"
        )

    test_client = http_client_class(connection_init_wait_timeout=timedelta(seconds=0))
    # Make sure the connection init timeout expired
    await asyncio.sleep(0.1)

    async with test_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        data = await ws.receive(timeout=2)
        assert ws.closed
        assert ws.close_code == 4408
        ws.assert_reason("Connection initialisation timeout")


async def test_connection_init_timeout_cancellation(
    http_client_class: Type[HttpClient],
):
    test_client = http_client_class(
        connection_init_wait_timeout=timedelta(milliseconds=50)
    )
    async with test_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.send_json(ConnectionInitMessage().as_dict())

        response = await ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

        await asyncio.sleep(0.1)

        await ws.send_json(
            SubscribeMessage(
                id="sub1",
                payload=SubscribeMessagePayload(
                    query="subscription { debug { isConnectionInitTimeoutTaskDone } }"
                ),
            ).as_dict()
        )

        response = await ws.receive_json()
        assert (
            response
            == NextMessage(
                id="sub1",
                payload={"data": {"debug": {"isConnectionInitTimeoutTaskDone": True}}},
            ).as_dict()
        )

        await ws.close()
        assert ws.closed
