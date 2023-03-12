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
    await ws.close()
    assert ws.closed


@pytest_asyncio.fixture
async def ws(ws_raw: WebSocketClient) -> WebSocketClient:
    await ws_raw.send_json(ConnectionInitMessage().as_dict())
    response = await ws_raw.receive_json()
    assert response == ConnectionAckMessage().as_dict()
    return ws_raw


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
    if ws.name() == "channels":
        ws.assert_reason("No text section for incoming WebSocket frame!")
    else:
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


async def test_too_many_initialisation_requests(ws: WebSocketClient):
    await ws.send_json(ConnectionInitMessage().as_dict())
    data = await ws.receive(timeout=2)
    assert ws.closed
    assert ws.close_code == 4429
    ws.assert_reason("Too many initialisation requests")


async def test_ping_pong(ws: WebSocketClient):
    await ws.send_json(PingMessage().as_dict())
    response = await ws.receive_json()
    assert response == PongMessage().as_dict()


async def test_server_sent_ping(ws: WebSocketClient):
    await ws.send_json(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(query="subscription { requestPing }"),
        ).as_dict()
    )

    response = await ws.receive_json()
    assert response == PingMessage().as_dict()

    await ws.send_json(PongMessage().as_dict())

    response = await ws.receive_json()
    assert (
        response
        == NextMessage(id="sub1", payload={"data": {"requestPing": True}}).as_dict()
    )

    response = await ws.receive_json()
    assert response == CompleteMessage(id="sub1").as_dict()


async def test_unauthorized_subscriptions(ws_raw: WebSocketClient):
    ws = ws_raw
    await ws.send_json(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(
                query='subscription { echo(message: "Hi") }'
            ),
        ).as_dict()
    )

    data = await ws.receive(timeout=2)
    assert ws.closed
    assert ws.close_code == 4401
    ws.assert_reason("Unauthorized")


async def test_duplicated_operation_ids(ws: WebSocketClient):
    await ws.send_json(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(
                query='subscription { echo(message: "Hi", delay: 5) }'
            ),
        ).as_dict()
    )

    await ws.send_json(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(
                query='subscription { echo(message: "Hi", delay: 5) }'
            ),
        ).as_dict()
    )

    data = await ws.receive(timeout=2)
    assert ws.closed
    assert ws.close_code == 4409
    ws.assert_reason("Subscriber for sub1 already exists")


async def test_reused_operation_ids(ws: WebSocketClient):
    """
    Test that an operation id can be re-used after it has been
    previously used for a completed operation
    """
    # Use sub1 as an id for an operation
    await ws.send_json(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(
                query='subscription { echo(message: "Hi") }'
            ),
        ).as_dict()
    )

    response = await ws.receive_json()
    assert (
        response
        == NextMessage(id="sub1", payload={"data": {"echo": "Hi"}}).as_dict()
    )

    response = await ws.receive_json()
    assert response == CompleteMessage(id="sub1").as_dict()

    # operation is now complete.  Create a new operation using
    # the same ID
    await ws.send_json(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(
                query='subscription { echo(message: "Hi") }'
            ),
        ).as_dict()
    )

    response = await ws.receive_json()
    assert (
        response
        == NextMessage(id="sub1", payload={"data": {"echo": "Hi"}}).as_dict()
    )


async def test_simple_subscription(ws: WebSocketClient):
    await ws.send_json(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(
                query='subscription { echo(message: "Hi") }'
            ),
        ).as_dict()
    )

    response = await ws.receive_json()
    assert (
        response
        == NextMessage(id="sub1", payload={"data": {"echo": "Hi"}}).as_dict()
    )

    await ws.send_json(CompleteMessage(id="sub1").as_dict())


async def test_subscription_syntax_error(ws: WebSocketClient):
    await ws.send_json(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(query="subscription { INVALID_SYNTAX "),
        ).as_dict()
    )

    data = await ws.receive(timeout=2)
    assert ws.closed
    assert ws.close_code == 4400
    ws.assert_reason("Syntax Error: Expected Name, found <EOF>.")


async def test_subscription_field_errors(ws: WebSocketClient):
    await ws.send_json(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(
                query="subscription { notASubscriptionField }",
            ),
        ).as_dict()
    )

    response = await ws.receive_json()
    assert response["type"] == ErrorMessage.type
    assert response["id"] == "sub1"
    assert len(response["payload"]) == 1
    assert response["payload"][0].get("path") is None
    assert response["payload"][0]["locations"] == [{"line": 1, "column": 16}]
    assert (
        response["payload"][0]["message"]
        == "The subscription field 'notASubscriptionField' is not defined."
    )


async def test_subscription_cancellation(ws: WebSocketClient):
    await ws.send_json(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(
                query='subscription { echo(message: "Hi", delay: 99) }'
            ),
        ).as_dict()
    )

    await ws.send_json(
        SubscribeMessage(
            id="sub2",
            payload=SubscribeMessagePayload(
                query="subscription { debug { numActiveResultHandlers } }",
            ),
        ).as_dict()
    )

    response = await ws.receive_json()
    assert (
        response
        == NextMessage(
            id="sub2", payload={"data": {"debug": {"numActiveResultHandlers": 2}}}
        ).as_dict()
    )

    response = await ws.receive_json()
    assert response == CompleteMessage(id="sub2").as_dict()

    await ws.send_json(CompleteMessage(id="sub1").as_dict())

    await ws.send_json(
        SubscribeMessage(
            id="sub3",
            payload=SubscribeMessagePayload(
                query="subscription { debug { numActiveResultHandlers } }",
            ),
        ).as_dict()
    )

    response = await ws.receive_json()
    assert (
        response
        == NextMessage(
            id="sub3", payload={"data": {"debug": {"numActiveResultHandlers": 1}}}
        ).as_dict()
    )

    response = await ws.receive_json()
    assert response == CompleteMessage(id="sub3").as_dict()


async def test_subscription_errors(ws: WebSocketClient):
    await ws.send_json(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(
                query='subscription { error(message: "TEST ERR") }',
            ),
        ).as_dict()
    )

    response = await ws.receive_json()
    assert response["type"] == ErrorMessage.type
    assert response["id"] == "sub1"
    assert len(response["payload"]) == 1
    assert response["payload"][0].get("path") == ["error"]
    assert response["payload"][0]["message"] == "TEST ERR"


async def test_subscription_error_no_complete(ws: WebSocketClient):
    """
    Test that an "error" message is not followed by "complete"
    """
    # get an "error" message
    await ws.send_json(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(
                query='subscription { error(message: "TEST ERR") }',
            ),
        ).as_dict()
    )

    response = await ws.receive_json()
    assert response["type"] == ErrorMessage.type
    assert response["id"] == "sub1"

    # after an "error" message, there should be nothing more
    # sent regarding "sub1", not even a "complete".
    await ws.send_json(
        SubscribeMessage(
            id="sub2",
            payload=SubscribeMessagePayload(
                query='subscription { error(message: "TEST ERR") }',
            ),
        ).as_dict()
    )
    response = await ws.receive_json()
    assert response["type"] == ErrorMessage.type
    assert response["id"] == "sub2"


async def test_subscription_exceptions(ws: WebSocketClient):
    await ws.send_json(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(
                query='subscription { exception(message: "TEST EXC") }',
            ),
        ).as_dict()
    )

    response = await ws.receive_json()
    assert response["type"] == ErrorMessage.type
    assert response["id"] == "sub1"
    assert len(response["payload"]) == 1
    assert response["payload"][0].get("path") is None
    assert response["payload"][0].get("locations") is None
    assert response["payload"][0]["message"] == "TEST EXC"
