from __future__ import annotations

import asyncio
import contextlib
import json
import time
from collections.abc import AsyncGenerator
from datetime import timedelta
from typing import TYPE_CHECKING, Optional, Union
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio
from pytest_mock import MockerFixture

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
)
from tests.http.clients.base import DebuggableGraphQLTransportWSHandler
from tests.views.schema import MyExtension, Schema

if TYPE_CHECKING:
    from tests.http.clients.base import HttpClient, WebSocketClient


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
    await ws_raw.send_message({"type": "connection_init"})
    connection_ack_message: ConnectionAckMessage = await ws_raw.receive_json()
    assert connection_ack_message == {"type": "connection_ack"}
    return ws_raw


def assert_next(
    next_message: NextMessage,
    id: str,
    data: dict[str, object],
    extensions: Optional[dict[str, object]] = None,
):
    """
    Assert that the NextMessage payload contains the provided data.
    If extensions is provided, it will also assert that the
    extensions are present
    """
    assert next_message["type"] == "next"
    assert next_message["id"] == id
    assert set(next_message["payload"].keys()) <= {"data", "errors", "extensions"}
    assert "data" in next_message["payload"]
    assert next_message["payload"]["data"] == data
    if extensions is not None:
        assert "extensions" in next_message["payload"]
        assert next_message["payload"]["extensions"] == extensions


async def test_unknown_message_type(ws_raw: WebSocketClient):
    ws = ws_raw

    await ws.send_json({"type": "NOT_A_MESSAGE_TYPE"})

    await ws.receive(timeout=2)
    assert ws.closed
    assert ws.close_code == 4400
    assert ws.close_reason == "Unknown message type: NOT_A_MESSAGE_TYPE"


async def test_missing_message_type(ws_raw: WebSocketClient):
    ws = ws_raw

    await ws.send_json({"notType": None})

    await ws.receive(timeout=2)
    assert ws.closed
    assert ws.close_code == 4400
    assert ws.close_reason == "Failed to parse message"


async def test_parsing_an_invalid_message(ws: WebSocketClient):
    await ws.send_json({"type": "subscribe", "notPayload": None})

    await ws.receive(timeout=2)
    assert ws.closed
    assert ws.close_code == 4400
    assert ws.close_reason == "Failed to parse message"


async def test_non_text_ws_messages_result_in_socket_closure(ws_raw: WebSocketClient):
    ws = ws_raw

    await ws.send_bytes(
        json.dumps(ConnectionInitMessage({"type": "connection_init"})).encode()
    )

    await ws.receive(timeout=2)
    assert ws.closed
    assert ws.close_code == 4400
    assert ws.close_reason == "WebSocket message type must be text"


async def test_non_json_ws_messages_result_in_socket_closure(ws_raw: WebSocketClient):
    ws = ws_raw

    await ws.send_text("not valid json")

    await ws.receive(timeout=2)
    assert ws.closed
    assert ws.close_code == 4400
    assert ws.close_reason == "WebSocket message must be valid JSON"


async def test_ws_message_frame_types_cannot_be_mixed(ws_raw: WebSocketClient):
    ws = ws_raw

    await ws.send_message({"type": "connection_init"})

    ack_message: ConnectionAckMessage = await ws.receive_json()
    assert ack_message == {"type": "connection_ack"}

    await ws.send_bytes(
        json.dumps(
            SubscribeMessage(
                {
                    "id": "sub1",
                    "type": "subscribe",
                    "payload": {
                        "query": "subscription { debug { isConnectionInitTimeoutTaskDone } }"
                    },
                }
            )
        ).encode()
    )

    await ws.receive(timeout=2)
    assert ws.closed
    assert ws.close_code == 4400
    assert ws.close_reason == "WebSocket message type must be text"


async def test_connection_init_timeout(
    request: object, http_client_class: type[HttpClient]
):
    with contextlib.suppress(ImportError):
        from tests.http.clients.aiohttp import AioHttpClient

        if http_client_class == AioHttpClient:
            pytest.skip(
                "Closing a AIOHTTP WebSocket from a "
                "task currently doesn't work as expected"
            )

    test_client = http_client_class()
    test_client.create_app(connection_init_wait_timeout=timedelta(seconds=0))

    async with test_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.receive(timeout=2)
        assert ws.closed
        assert ws.close_code == 4408
        assert ws.close_reason == "Connection initialisation timeout"


@pytest.mark.flaky
async def test_connection_init_timeout_cancellation(
    ws_raw: WebSocketClient,
):
    # Verify that the timeout task is cancelled after the connection Init
    # message is received
    ws = ws_raw
    await ws.send_message({"type": "connection_init"})

    connection_ack_message: ConnectionAckMessage = await ws.receive_json()
    assert connection_ack_message == {"type": "connection_ack"}

    await ws.send_message(
        {
            "id": "sub1",
            "type": "subscribe",
            "payload": {
                "query": "subscription { debug { isConnectionInitTimeoutTaskDone } }"
            },
        }
    )

    next_message: NextMessage = await ws.receive_json()
    assert_next(
        next_message, "sub1", {"debug": {"isConnectionInitTimeoutTaskDone": True}}
    )


@pytest.mark.xfail(reason="This test is flaky")
async def test_close_twice(
    mocker: MockerFixture, request: object, http_client_class: type[HttpClient]
):
    test_client = http_client_class()
    test_client.create_app(connection_init_wait_timeout=timedelta(seconds=0.25))

    async with test_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        transport_close = mocker.patch.object(ws, "close")

        # We set payload is set to "invalid value" to force a invalid payload error
        # which will close the connection
        await ws.send_json({"type": "connection_init", "payload": "invalid value"})

        # Yield control so that ._close can be called
        await asyncio.sleep(0)

        for t in asyncio.all_tasks():
            if (
                t.get_coro().__qualname__
                == "BaseGraphQLTransportWSHandler.handle_connection_init_timeout"
            ):
                # The init timeout task should be cancelled
                with pytest.raises(asyncio.CancelledError):
                    await t

        await ws.receive(timeout=0.5)
        assert ws.closed
        assert ws.close_code == 4400
        assert ws.close_reason == "Invalid connection init payload"
        transport_close.assert_not_called()


async def test_too_many_initialisation_requests(ws: WebSocketClient):
    await ws.send_message({"type": "connection_init"})
    await ws.receive(timeout=2)
    assert ws.closed
    assert ws.close_code == 4429
    assert ws.close_reason == "Too many initialisation requests"


async def test_connections_are_accepted_by_default(ws_raw: WebSocketClient):
    await ws_raw.send_message({"type": "connection_init"})
    connection_ack_message: ConnectionAckMessage = await ws_raw.receive_json()
    assert connection_ack_message == {"type": "connection_ack"}

    await ws_raw.close()
    assert ws_raw.closed


@pytest.mark.parametrize("payload", [None, {"token": "secret"}])
async def test_setting_a_connection_ack_payload(ws_raw: WebSocketClient, payload):
    await ws_raw.send_message(
        {
            "type": "connection_init",
            "payload": {"test-accept": True, "ack-payload": payload},
        }
    )

    connection_ack_message: ConnectionAckMessage = await ws_raw.receive_json()
    assert connection_ack_message == {"type": "connection_ack", "payload": payload}

    await ws_raw.close()
    assert ws_raw.closed


async def test_connection_ack_payload_may_be_unset(ws_raw: WebSocketClient):
    await ws_raw.send_message(
        {
            "type": "connection_init",
            "payload": {"test-accept": True},
        }
    )

    connection_ack_message: ConnectionAckMessage = await ws_raw.receive_json()
    assert connection_ack_message == {"type": "connection_ack"}

    await ws_raw.close()
    assert ws_raw.closed


async def test_rejecting_connection_closes_socket_with_expected_code_and_message(
    ws_raw: WebSocketClient,
):
    await ws_raw.send_message(
        {"type": "connection_init", "payload": {"test-reject": True}}
    )

    await ws_raw.receive(timeout=2)
    assert ws_raw.closed
    assert ws_raw.close_code == 4403
    assert ws_raw.close_reason == "Forbidden"


async def test_context_can_be_modified_from_within_on_ws_connect(
    ws_raw: WebSocketClient,
):
    await ws_raw.send_message(
        {
            "type": "connection_init",
            "payload": {"test-modify": True},
        }
    )

    connection_ack_message: ConnectionAckMessage = await ws_raw.receive_json()
    assert connection_ack_message == {"type": "connection_ack"}

    await ws_raw.send_message(
        {
            "type": "subscribe",
            "id": "demo",
            "payload": {
                "query": "subscription { connectionParams }",
            },
        }
    )

    next_message: NextMessage = await ws_raw.receive_json()
    assert next_message["type"] == "next"
    assert next_message["id"] == "demo"
    assert "data" in next_message["payload"]
    assert next_message["payload"]["data"] == {
        "connectionParams": {"test-modify": True, "modified": True}
    }

    await ws_raw.close()
    assert ws_raw.closed


async def test_ping_pong(ws: WebSocketClient):
    await ws.send_message({"type": "ping"})
    pong_message: PongMessage = await ws.receive_json()
    assert pong_message == {"type": "pong"}


async def test_can_send_payload_with_additional_things(ws_raw: WebSocketClient):
    ws = ws_raw

    # send  init

    await ws.send_message({"type": "connection_init"})

    await ws.receive(timeout=2)

    await ws.send_message(
        {
            "type": "subscribe",
            "payload": {
                "query": 'subscription { echo(message: "Hi") }',
                "extensions": {
                    "some": "other thing",
                },
            },
            "id": "1",
        }
    )

    next_message: NextMessage = await ws.receive_json(timeout=2)

    assert next_message == {
        "type": "next",
        "id": "1",
        "payload": {"data": {"echo": "Hi"}, "extensions": {"example": "example"}},
    }


async def test_server_sent_ping(ws: WebSocketClient):
    await ws.send_message(
        {
            "id": "sub1",
            "type": "subscribe",
            "payload": {"query": "subscription { requestPing }"},
        }
    )

    ping_message: PingMessage = await ws.receive_json()
    assert ping_message == {"type": "ping"}

    await ws.send_message({"type": "pong"})

    next_message: NextMessage = await ws.receive_json()
    assert_next(next_message, "sub1", {"requestPing": True})

    complete_message: CompleteMessage = await ws.receive_json()
    assert complete_message == {"id": "sub1", "type": "complete"}


async def test_unauthorized_subscriptions(ws_raw: WebSocketClient):
    ws = ws_raw
    await ws.send_message(
        {
            "id": "sub1",
            "type": "subscribe",
            "payload": {"query": 'subscription { echo(message: "Hi") }'},
        }
    )

    await ws.receive(timeout=2)
    assert ws.closed
    assert ws.close_code == 4401
    assert ws.close_reason == "Unauthorized"


async def test_duplicated_operation_ids(ws: WebSocketClient):
    await ws.send_message(
        {
            "id": "sub1",
            "type": "subscribe",
            "payload": {"query": 'subscription { echo(message: "Hi", delay: 5) }'},
        }
    )

    await ws.send_message(
        {
            "id": "sub1",
            "type": "subscribe",
            "payload": {"query": 'subscription { echo(message: "Hi", delay: 5) }'},
        }
    )

    await ws.receive(timeout=2)
    assert ws.closed
    assert ws.close_code == 4409
    assert ws.close_reason == "Subscriber for sub1 already exists"


async def test_reused_operation_ids(ws: WebSocketClient):
    """Test that an operation id can be re-used after it has been
    previously used for a completed operation.
    """
    # Use sub1 as an id for an operation
    await ws.send_message(
        {
            "id": "sub1",
            "type": "subscribe",
            "payload": {"query": 'subscription { echo(message: "Hi") }'},
        }
    )

    next_message1: NextMessage = await ws.receive_json()
    assert_next(next_message1, "sub1", {"echo": "Hi"})

    complete_message: CompleteMessage = await ws.receive_json()
    assert complete_message == {"id": "sub1", "type": "complete"}

    # operation is now complete.  Create a new operation using
    # the same ID
    await ws.send_message(
        {
            "id": "sub1",
            "type": "subscribe",
            "payload": {"query": 'subscription { echo(message: "Hi") }'},
        }
    )

    next_message2: NextMessage = await ws.receive_json()
    assert_next(next_message2, "sub1", {"echo": "Hi"})


async def test_simple_subscription(ws: WebSocketClient):
    await ws.send_message(
        {
            "id": "sub1",
            "type": "subscribe",
            "payload": {"query": 'subscription { echo(message: "Hi") }'},
        }
    )

    next_message: NextMessage = await ws.receive_json()
    assert_next(next_message, "sub1", {"echo": "Hi"})
    await ws.send_message({"id": "sub1", "type": "complete"})


async def test_subscription_syntax_error(ws: WebSocketClient):
    await ws.send_message(
        {
            "id": "sub1",
            "type": "subscribe",
            "payload": {"query": "subscription { INVALID_SYNTAX "},
        }
    )

    await ws.receive(timeout=2)
    assert ws.closed
    assert ws.close_code == 4400
    assert ws.close_reason == "Syntax Error: Expected Name, found <EOF>."


async def test_subscription_field_errors(ws: WebSocketClient):
    process_errors = Mock()
    with patch.object(Schema, "process_errors", process_errors):
        await ws.send_message(
            {
                "id": "sub1",
                "type": "subscribe",
                "payload": {
                    "query": "subscription { notASubscriptionField }",
                },
            }
        )

        error_message: ErrorMessage = await ws.receive_json()
        assert error_message["type"] == "error"
        assert error_message["id"] == "sub1"
        assert len(error_message["payload"]) == 1

        assert "locations" in error_message["payload"][0]
        assert error_message["payload"][0]["locations"] == [{"line": 1, "column": 16}]

        assert "message" in error_message["payload"][0]
        assert (
            error_message["payload"][0]["message"]
            == "Cannot query field 'notASubscriptionField' on type 'Subscription'."
        )

        process_errors.assert_called_once()


async def test_subscription_cancellation(ws: WebSocketClient):
    await ws.send_message(
        {
            "id": "sub1",
            "type": "subscribe",
            "payload": {"query": 'subscription { echo(message: "Hi", delay: 99) }'},
        }
    )

    await ws.send_message(
        {
            "id": "sub2",
            "type": "subscribe",
            "payload": {
                "query": "subscription { debug { numActiveResultHandlers } }",
            },
        }
    )

    next_message: NextMessage = await ws.receive_json()
    assert_next(next_message, "sub2", {"debug": {"numActiveResultHandlers": 2}})

    complete_message: CompleteMessage = await ws.receive_json()
    assert complete_message == {"id": "sub2", "type": "complete"}

    await ws.send_message({"id": "sub1", "type": "complete"})

    await ws.send_message(
        {
            "id": "sub3",
            "type": "subscribe",
            "payload": {
                "query": "subscription { debug { numActiveResultHandlers } }",
            },
        }
    )

    next_message: NextMessage = await ws.receive_json()
    assert_next(next_message, "sub3", {"debug": {"numActiveResultHandlers": 1}})

    complete_message: CompleteMessage = await ws.receive_json()
    assert complete_message == {"id": "sub3", "type": "complete"}


async def test_subscription_errors(ws: WebSocketClient):
    await ws.send_message(
        {
            "id": "sub1",
            "type": "subscribe",
            "payload": {
                "query": 'subscription { error(message: "TEST ERR") }',
            },
        }
    )

    next_message: NextMessage = await ws.receive_json()
    assert next_message["type"] == "next"
    assert next_message["id"] == "sub1"

    assert "errors" in next_message["payload"]
    payload_errors = next_message["payload"]["errors"]
    assert payload_errors is not None
    assert len(payload_errors) == 1

    assert "path" in payload_errors[0]
    assert payload_errors[0]["path"] == ["error"]

    assert "message" in payload_errors[0]
    assert payload_errors[0]["message"] == "TEST ERR"


async def test_operation_error_no_complete(ws: WebSocketClient):
    """Test that an "error" message is not followed by "complete"."""
    # Since we don't include the operation variables,
    # the subscription will fail immediately.
    # see https://github.com/enisdenjo/graphql-ws/blob/master/PROTOCOL.md#error
    await ws.send_message(
        {
            "id": "sub1",
            "type": "subscribe",
            "payload": {
                "query": "subscription Foo($bar: String!){ exception(message: $bar) }",
            },
        }
    )

    error_message: ErrorMessage = await ws.receive_json()
    assert error_message["type"] == "error"
    assert error_message["id"] == "sub1"

    # after an "error" message, there should be nothing more
    # sent regarding "sub1", not even a "complete".
    await ws.send_message({"type": "ping"})

    pong_message: PongMessage = await ws.receive_json(timeout=1)
    assert pong_message == {"type": "pong"}


async def test_subscription_exceptions(ws: WebSocketClient):
    process_errors = Mock()
    with patch.object(Schema, "process_errors", process_errors):
        await ws.send_message(
            {
                "id": "sub1",
                "type": "subscribe",
                "payload": {
                    "query": 'subscription { exception(message: "TEST EXC") }',
                },
            }
        )

        next_message: NextMessage = await ws.receive_json()
        assert next_message["type"] == "next"
        assert next_message["id"] == "sub1"
        assert "errors" in next_message["payload"]
        assert next_message["payload"]["errors"] == [{"message": "TEST EXC"}]
        process_errors.assert_called_once()


async def test_single_result_query_operation(ws: WebSocketClient):
    await ws.send_message(
        {
            "id": "sub1",
            "type": "subscribe",
            "payload": {"query": "query { hello }"},
        }
    )

    next_message: NextMessage = await ws.receive_json()
    assert_next(next_message, "sub1", {"hello": "Hello world"})

    complete_message: CompleteMessage = await ws.receive_json()
    assert complete_message == {"id": "sub1", "type": "complete"}


async def test_single_result_query_operation_async(ws: WebSocketClient):
    """Test a single result query operation on an
    `async` method in the schema, including an artificial
    async delay.
    """
    await ws.send_message(
        {
            "id": "sub1",
            "type": "subscribe",
            "payload": {"query": 'query { asyncHello(name: "Dolly", delay:0.01)}'},
        }
    )

    next_message: NextMessage = await ws.receive_json()
    assert_next(next_message, "sub1", {"asyncHello": "Hello Dolly"})

    complete_message: CompleteMessage = await ws.receive_json()
    assert complete_message == {"id": "sub1", "type": "complete"}


async def test_single_result_query_operation_overlapped(ws: WebSocketClient):
    """Test that two single result queries can be in flight at the same time,
    just like regular queries.  Start two queries with separate ids. The
    first query has a delay, so we expect the message to the second
    query to be delivered first.
    """
    # first query
    await ws.send_message(
        {
            "id": "sub1",
            "type": "subscribe",
            "payload": {"query": 'query { asyncHello(name: "Dolly", delay:1)}'},
        }
    )
    # second query
    await ws.send_message(
        {
            "id": "sub2",
            "type": "subscribe",
            "payload": {"query": 'query { asyncHello(name: "Dolly", delay:0)}'},
        }
    )

    # we expect the message to the second query to arrive first
    next_message: NextMessage = await ws.receive_json()
    assert_next(next_message, "sub2", {"asyncHello": "Hello Dolly"})

    complete_message: CompleteMessage = await ws.receive_json()
    assert complete_message == {"id": "sub2", "type": "complete"}


async def test_single_result_mutation_operation(ws: WebSocketClient):
    await ws.send_message(
        {
            "id": "sub1",
            "type": "subscribe",
            "payload": {"query": "mutation { hello }"},
        }
    )

    next_message: NextMessage = await ws.receive_json()
    assert_next(next_message, "sub1", {"hello": "strawberry"})

    complete_message: CompleteMessage = await ws.receive_json()
    assert complete_message == {"id": "sub1", "type": "complete"}


async def test_single_result_operation_selection(ws: WebSocketClient):
    query = """
        query Query1 {
            hello
        }
        query Query2 {
            hello(name: "Strawberry")
        }
    """

    await ws.send_message(
        {
            "id": "sub1",
            "type": "subscribe",
            "payload": {"query": query, "operationName": "Query2"},
        }
    )

    next_message: NextMessage = await ws.receive_json()
    assert_next(next_message, "sub1", {"hello": "Hello Strawberry"})

    complete_message: CompleteMessage = await ws.receive_json()
    assert complete_message == {"id": "sub1", "type": "complete"}


async def test_single_result_invalid_operation_selection(ws: WebSocketClient):
    query = """
        query Query1 {
            hello
        }
    """

    await ws.send_message(
        {
            "id": "sub1",
            "type": "subscribe",
            "payload": {"query": query, "operationName": "Query2"},
        }
    )

    await ws.receive(timeout=2)
    assert ws.closed
    assert ws.close_code == 4400
    assert ws.close_reason == "Can't get GraphQL operation type"


async def test_single_result_execution_error(ws: WebSocketClient):
    process_errors = Mock()
    with patch.object(Schema, "process_errors", process_errors):
        await ws.send_message(
            {
                "id": "sub1",
                "type": "subscribe",
                "payload": {
                    "query": "query { alwaysFail }",
                },
            }
        )

        next_message: NextMessage = await ws.receive_json()
        assert next_message["type"] == "next"
        assert next_message["id"] == "sub1"

        assert "errors" in next_message["payload"]
        payload_errors = next_message["payload"]["errors"]
        assert payload_errors is not None
        assert len(payload_errors) == 1

        assert "path" in payload_errors[0]
        assert payload_errors[0]["path"] == ["alwaysFail"]

        assert "message" in payload_errors[0]
        assert payload_errors[0]["message"] == "You are not authorized"

        process_errors.assert_called_once()


async def test_single_result_pre_execution_error(ws: WebSocketClient):
    """Test that single-result-operations which raise exceptions
    behave in the same way as streaming operations.
    """
    process_errors = Mock()
    with patch.object(Schema, "process_errors", process_errors):
        await ws.send_message(
            {
                "id": "sub1",
                "type": "subscribe",
                "payload": {
                    "query": "query { IDontExist }",
                },
            }
        )

        error_message: ErrorMessage = await ws.receive_json()
        assert error_message["type"] == "error"
        assert error_message["id"] == "sub1"
        assert len(error_message["payload"]) == 1
        assert "message" in error_message["payload"][0]
        assert (
            error_message["payload"][0]["message"]
            == "Cannot query field 'IDontExist' on type 'Query'."
        )
        process_errors.assert_called_once()


async def test_single_result_duplicate_ids_sub(ws: WebSocketClient):
    """Test that single-result-operations and streaming operations
    share the same ID namespace. Start a regular subscription,
    then issue a single-result operation with same ID and expect an
    error due to already existing ID
    """
    # regular subscription
    await ws.send_message(
        {
            "id": "sub1",
            "type": "subscribe",
            "payload": {"query": 'subscription { echo(message: "Hi", delay: 5) }'},
        }
    )
    # single result subscription with duplicate id
    await ws.send_message(
        {
            "id": "sub1",
            "type": "subscribe",
            "payload": {
                "query": "query { hello }",
            },
        }
    )

    await ws.receive(timeout=2)
    assert ws.closed
    assert ws.close_code == 4409
    assert ws.close_reason == "Subscriber for sub1 already exists"


async def test_single_result_duplicate_ids_query(ws: WebSocketClient):
    """Test that single-result-operations don't allow duplicate
    IDs for two asynchronous queries. Issue one async query
    with delay, then another with same id. Expect error.
    """
    # single result subscription 1
    await ws.send_message(
        {
            "id": "sub1",
            "type": "subscribe",
            "payload": {"query": 'query { asyncHello(name: "Hi", delay: 5) }'},
        }
    )
    # single result subscription with duplicate id
    await ws.send_message(
        {
            "id": "sub1",
            "type": "subscribe",
            "payload": {
                "query": "query { hello }",
            },
        }
    )

    # We expect the remote to close the socket due to duplicate ID in use
    await ws.receive(timeout=2)
    assert ws.closed
    assert ws.close_code == 4409
    assert ws.close_reason == "Subscriber for sub1 already exists"


async def test_injects_connection_params(ws_raw: WebSocketClient):
    ws = ws_raw
    await ws.send_message(
        {"type": "connection_init", "payload": {"strawberry": "rocks"}}
    )

    connection_ack_message: ConnectionAckMessage = await ws.receive_json()
    assert connection_ack_message == {"type": "connection_ack"}

    await ws.send_message(
        {
            "id": "sub1",
            "type": "subscribe",
            "payload": {"query": "subscription { connectionParams }"},
        }
    )

    next_message: NextMessage = await ws.receive_json()
    assert_next(next_message, "sub1", {"connectionParams": {"strawberry": "rocks"}})

    await ws.send_message({"id": "sub1", "type": "complete"})


async def test_rejects_connection_params_not_dict(ws_raw: WebSocketClient):
    ws = ws_raw
    await ws.send_json({"type": "connection_init", "payload": "gonna fail"})

    await ws.receive(timeout=2)
    assert ws.closed
    assert ws.close_code == 4400
    assert ws.close_reason == "Invalid connection init payload"


@pytest.mark.parametrize(
    "payload",
    [[], "invalid value", 1],
)
async def test_rejects_connection_params_with_wrong_type(
    payload: object, ws_raw: WebSocketClient
):
    ws = ws_raw
    await ws.send_json({"type": "connection_init", "payload": payload})

    await ws.receive(timeout=2)
    assert ws.closed
    assert ws.close_code == 4400
    assert ws.close_reason == "Invalid connection init payload"


# timings can sometimes fail currently.  Until this test is rewritten when
# generator based subscriptions are implemented, mark it as flaky
@pytest.mark.xfail(reason="This test is flaky, see comment above")
async def test_subsciption_cancel_finalization_delay(ws: WebSocketClient):
    # Test that when we cancel a subscription, the websocket isn't blocked
    # while some complex finalization takes place.
    delay = 0.1

    await ws.send_message(
        {
            "id": "sub1",
            "type": "subscribe",
            "payload": {"query": f"subscription {{ longFinalizer(delay: {delay}) }}"},
        }
    )

    next_message: NextMessage = await ws.receive_json()
    assert_next(next_message, "sub1", {"longFinalizer": "hello"})

    # now cancel the stubscription and send a new query. We expect the message
    # to the new query to arrive immediately, without waiting for the finalizer
    start = time.time()
    await ws.send_message({"id": "sub1", "type": "complete"})
    await ws.send_message(
        {
            "id": "sub2",
            "type": "subscribe",
            "payload": {"query": "query { hello }"},
        }
    )

    while True:
        next_or_complete_message: Union[
            NextMessage, CompleteMessage
        ] = await ws.receive_json()

        assert next_or_complete_message["type"] in ("next", "complete")

        if next_or_complete_message["id"] == "sub2":
            break

    end = time.time()
    elapsed = end - start
    assert elapsed < delay


async def test_error_handler_for_timeout(http_client: HttpClient):
    """Test that the error handler is called when the timeout
    task encounters an error.
    """
    with contextlib.suppress(ImportError):
        from tests.http.clients.channels import ChannelsHttpClient

        if isinstance(http_client, ChannelsHttpClient):
            pytest.skip("Can't patch on_init for this client")

    if not AsyncMock:
        pytest.skip("Don't have AsyncMock")

    ws = ws_raw
    handler = None
    errorhandler = AsyncMock()

    def on_init(_handler):
        nonlocal handler
        if handler:
            return
        handler = _handler
        # patch the object
        handler.handle_task_exception = errorhandler
        # cause an attribute error in the timeout task
        handler.connection_init_wait_timeout = None

    with patch.object(DebuggableGraphQLTransportWSHandler, "on_init", on_init):
        async with http_client.ws_connect(
            "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
        ) as ws:
            await asyncio.sleep(0.01)  # wait for the timeout task to start
            await ws.send_message({"type": "connection_init"})
            connection_ack_message: ConnectionAckMessage = await ws.receive_json()
            assert connection_ack_message == {"type": "connection_ack"}
            await ws.close()

    # the error hander should have been called
    assert handler
    errorhandler.assert_called_once()
    args = errorhandler.call_args
    assert isinstance(args[0][0], AttributeError)
    assert "total_seconds" in str(args[0][0])


async def test_subscription_errors_continue(ws: WebSocketClient):
    """Verify that an ExecutionResult with errors during subscription does not terminate
    the subscription.
    """
    process_errors = Mock()
    with patch.object(Schema, "process_errors", process_errors):
        await ws.send_message(
            {
                "id": "sub1",
                "type": "subscribe",
                "payload": {
                    "query": "subscription { flavorsInvalid }",
                },
            }
        )

        next_message1: NextMessage = await ws.receive_json()
        assert next_message1["type"] == "next"
        assert next_message1["id"] == "sub1"
        assert "data" in next_message1["payload"]
        assert next_message1["payload"]["data"] == {"flavorsInvalid": "VANILLA"}

        next_message2: NextMessage = await ws.receive_json()
        assert next_message2["type"] == "next"
        assert next_message2["id"] == "sub1"
        assert "data" in next_message2["payload"]
        assert next_message2["payload"]["data"] is None
        assert "errors" in next_message2["payload"]
        assert "cannot represent value" in str(next_message2["payload"]["errors"])
        process_errors.assert_called_once()

        next_message3: NextMessage = await ws.receive_json()
        assert next_message3["type"] == "next"
        assert next_message3["id"] == "sub1"
        assert "data" in next_message3["payload"]
        assert next_message3["payload"]["data"] == {"flavorsInvalid": "CHOCOLATE"}

        complete_message: CompleteMessage = await ws.receive_json()
        assert complete_message["type"] == "complete"
        assert complete_message["id"] == "sub1"


@patch.object(MyExtension, MyExtension.get_results.__name__, return_value={})
async def test_no_extensions_results_wont_send_extensions_in_payload(
    mock: Mock, ws: WebSocketClient
):
    await ws.send_message(
        {
            "id": "sub1",
            "type": "subscribe",
            "payload": {"query": 'subscription { echo(message: "Hi") }'},
        }
    )

    next_message: NextMessage = await ws.receive_json()
    mock.assert_called_once()
    assert_next(next_message, "sub1", {"echo": "Hi"})
    assert "extensions" not in next_message["payload"]


async def test_unexpected_client_disconnects_are_gracefully_handled(
    ws: WebSocketClient,
):
    process_errors = Mock()

    with patch.object(Schema, "process_errors", process_errors):
        await ws.send_message(
            {
                "id": "sub1",
                "type": "subscribe",
                "payload": {
                    "query": 'subscription { echo(message: "Hi", delay: 0.5) }'
                },
            }
        )

        await ws.close()
        await asyncio.sleep(1)
        assert not process_errors.called
