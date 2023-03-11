
import asyncio
import json
from datetime import timedelta

import pytest
from ..http.clients import HttpClient

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
from tests.aiohttp.app import create_app


async def test_unknown_message_type(http_client: HttpClient):

    async with http_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.send_json({"type": "NOT_A_MESSAGE_TYPE"})

        data = await ws.receive(timeout=2)
        assert ws.closed
        assert ws.close_code == 4400
        assert data.extra == "Unknown message type: NOT_A_MESSAGE_TYPE"
