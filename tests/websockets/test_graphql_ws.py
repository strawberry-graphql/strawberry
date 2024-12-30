from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Union
from unittest import mock

import pytest
import pytest_asyncio

from strawberry.subscriptions import GRAPHQL_WS_PROTOCOL
from strawberry.subscriptions.protocols.graphql_ws.types import (
    CompleteMessage,
    ConnectionAckMessage,
    ConnectionErrorMessage,
    ConnectionInitMessage,
    ConnectionKeepAliveMessage,
    DataMessage,
    ErrorMessage,
    StartMessage,
)
from tests.views.schema import MyExtension, Schema

if TYPE_CHECKING:
    from tests.http.clients.aiohttp import HttpClient, WebSocketClient


@pytest_asyncio.fixture
async def ws_raw(http_client: HttpClient) -> AsyncGenerator[WebSocketClient, None]:
    async with http_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_WS_PROTOCOL]
    ) as ws:
        yield ws
        await ws.close()
        assert ws.closed


@pytest_asyncio.fixture
async def ws(ws_raw: WebSocketClient) -> AsyncGenerator[WebSocketClient, None]:
    ws = ws_raw

    await ws.send_legacy_message({"type": "connection_init"})
    response: ConnectionAckMessage = await ws.receive_json()
    assert response["type"] == "connection_ack"

    yield ws

    await ws.send_legacy_message({"type": "connection_terminate"})
    # make sure the WebSocket is disconnected now
    await ws.receive(timeout=2)  # receive close
    assert ws.closed


# convenience fixture to use previous name
@pytest.fixture
def aiohttp_app_client(http_client: HttpClient) -> HttpClient:
    return http_client


async def test_simple_subscription(ws: WebSocketClient):
    await ws.send_legacy_message(
        {
            "type": "start",
            "id": "demo",
            "payload": {
                "query": 'subscription { echo(message: "Hi") }',
            },
        }
    )

    data_message: DataMessage = await ws.receive_json()
    assert data_message["type"] == "data"
    assert data_message["id"] == "demo"
    assert data_message["payload"]["data"] == {"echo": "Hi"}

    await ws.send_legacy_message({"type": "stop", "id": "demo"})

    complete_message: CompleteMessage = await ws.receive_json()
    assert complete_message["type"] == "complete"
    assert complete_message["id"] == "demo"


async def test_operation_selection(ws: WebSocketClient):
    await ws.send_legacy_message(
        {
            "type": "start",
            "id": "demo",
            "payload": {
                "query": """
                    subscription Subscription1 { echo(message: "Hi1") }
                    subscription Subscription2 { echo(message: "Hi2") }
                """,
                "operationName": "Subscription2",
            },
        }
    )

    data_message: DataMessage = await ws.receive_json()
    assert data_message["type"] == "data"
    assert data_message["id"] == "demo"
    assert data_message["payload"]["data"] == {"echo": "Hi2"}

    await ws.send_legacy_message({"type": "stop", "id": "demo"})

    complete_message: CompleteMessage = await ws.receive_json()
    assert complete_message["type"] == "complete"
    assert complete_message["id"] == "demo"


async def test_connections_are_accepted_by_default(ws_raw: WebSocketClient):
    await ws_raw.send_legacy_message({"type": "connection_init"})
    connection_ack_message: ConnectionAckMessage = await ws_raw.receive_json()
    assert connection_ack_message == {"type": "connection_ack"}

    await ws_raw.close()
    assert ws_raw.closed


async def test_setting_a_connection_ack_payload(ws_raw: WebSocketClient):
    await ws_raw.send_legacy_message(
        {
            "type": "connection_init",
            "payload": {"test-accept": True, "ack-payload": {"token": "secret"}},
        }
    )

    connection_ack_message: ConnectionAckMessage = await ws_raw.receive_json()
    assert connection_ack_message == {
        "type": "connection_ack",
        "payload": {"token": "secret"},
    }

    await ws_raw.close()
    assert ws_raw.closed


async def test_connection_ack_payload_may_be_unset(ws_raw: WebSocketClient):
    await ws_raw.send_legacy_message(
        {
            "type": "connection_init",
            "payload": {"test-accept": True},
        }
    )

    connection_ack_message: ConnectionAckMessage = await ws_raw.receive_json()
    assert connection_ack_message == {"type": "connection_ack"}

    await ws_raw.close()
    assert ws_raw.closed


async def test_a_connection_ack_payload_of_none_is_treated_as_unset(
    ws_raw: WebSocketClient,
):
    await ws_raw.send_legacy_message(
        {
            "type": "connection_init",
            "payload": {"test-accept": True, "ack-payload": None},
        }
    )

    connection_ack_message: ConnectionAckMessage = await ws_raw.receive_json()
    assert connection_ack_message == {"type": "connection_ack"}

    await ws_raw.close()
    assert ws_raw.closed


async def test_rejecting_connection_results_in_error_message_and_socket_closure(
    ws_raw: WebSocketClient,
):
    await ws_raw.send_legacy_message(
        {"type": "connection_init", "payload": {"test-reject": True}}
    )

    connection_error_message: ConnectionErrorMessage = await ws_raw.receive_json()
    assert connection_error_message == {"type": "connection_error", "payload": {}}

    await ws_raw.receive(timeout=2)
    assert ws_raw.closed
    assert ws_raw.close_code == 1011
    assert not ws_raw.close_reason


async def test_rejecting_connection_with_custom_connection_error_payload(
    ws_raw: WebSocketClient,
):
    await ws_raw.send_legacy_message(
        {
            "type": "connection_init",
            "payload": {"test-reject": True, "err-payload": {"custom": "error"}},
        }
    )

    connection_error_message: ConnectionErrorMessage = await ws_raw.receive_json()
    assert connection_error_message == {
        "type": "connection_error",
        "payload": {"custom": "error"},
    }

    await ws_raw.receive(timeout=2)
    assert ws_raw.closed
    assert ws_raw.close_code == 1011
    assert not ws_raw.close_reason


async def test_context_can_be_modified_from_within_on_ws_connect(
    ws_raw: WebSocketClient,
):
    await ws_raw.send_legacy_message(
        {
            "type": "connection_init",
            "payload": {"test-modify": True},
        }
    )

    connection_ack_message: ConnectionAckMessage = await ws_raw.receive_json()
    assert connection_ack_message == {"type": "connection_ack"}

    await ws_raw.send_legacy_message(
        {
            "type": "start",
            "id": "demo",
            "payload": {
                "query": "subscription { connectionParams }",
            },
        }
    )

    data_message: DataMessage = await ws_raw.receive_json()
    assert data_message["type"] == "data"
    assert data_message["id"] == "demo"
    assert data_message["payload"]["data"] == {
        "connectionParams": {"test-modify": True, "modified": True}
    }

    await ws_raw.close()
    assert ws_raw.closed


async def test_sends_keep_alive(aiohttp_app_client: HttpClient):
    aiohttp_app_client.create_app(keep_alive=True, keep_alive_interval=0.1)
    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_WS_PROTOCOL]
    ) as ws:
        await ws.send_legacy_message({"type": "connection_init"})
        await ws.send_legacy_message(
            {
                "type": "start",
                "id": "demo",
                "payload": {
                    "query": 'subscription { echo(message: "Hi", delay: 0.15) }',
                },
            }
        )

        ack_message: ConnectionAckMessage = await ws.receive_json()
        assert ack_message["type"] == "connection_ack"

        # we can't be sure how many keep-alives exactly we
        # get but they should be more than one.
        keepalive_count = 0
        while True:
            ka_or_data_message: Union[
                ConnectionKeepAliveMessage, DataMessage
            ] = await ws.receive_json()
            if ka_or_data_message["type"] == "ka":
                keepalive_count += 1
            else:
                break
        assert keepalive_count >= 1

        assert ka_or_data_message["type"] == "data"
        assert ka_or_data_message["id"] == "demo"
        assert ka_or_data_message["payload"]["data"] == {"echo": "Hi"}

        complete_message: CompleteMessage = await ws.receive_json()
        assert complete_message["type"] == "complete"
        assert complete_message["id"] == "demo"

        await ws.send_legacy_message({"type": "connection_terminate"})


async def test_subscription_cancellation(ws: WebSocketClient):
    await ws.send_legacy_message(
        {
            "type": "start",
            "id": "demo",
            "payload": {"query": 'subscription { echo(message: "Hi", delay: 99) }'},
        }
    )

    await ws.send_legacy_message(
        {
            "type": "start",
            "id": "debug1",
            "payload": {
                "query": "subscription { debug { numActiveResultHandlers } }",
            },
        }
    )

    data_message: DataMessage = await ws.receive_json()
    assert data_message["type"] == "data"
    assert data_message["id"] == "debug1"
    assert data_message["payload"]["data"] == {"debug": {"numActiveResultHandlers": 2}}

    complete_message1 = await ws.receive_json()
    assert complete_message1["type"] == "complete"
    assert complete_message1["id"] == "debug1"

    await ws.send_legacy_message({"type": "stop", "id": "demo"})

    complete_message2 = await ws.receive_json()
    assert complete_message2["type"] == "complete"
    assert complete_message2["id"] == "demo"

    await ws.send_legacy_message(
        {
            "type": "start",
            "id": "debug2",
            "payload": {
                "query": "subscription { debug { numActiveResultHandlers} }",
            },
        }
    )

    data_message2 = await ws.receive_json()
    assert data_message2["type"] == "data"
    assert data_message2["id"] == "debug2"
    assert data_message2["payload"]["data"] == {"debug": {"numActiveResultHandlers": 1}}

    complete_message3: CompleteMessage = await ws.receive_json()
    assert complete_message3["type"] == "complete"
    assert complete_message3["id"] == "debug2"


async def test_subscription_errors(ws: WebSocketClient):
    await ws.send_legacy_message(
        {
            "type": "start",
            "id": "demo",
            "payload": {"query": 'subscription { error(message: "TEST ERR") }'},
        }
    )

    data_message: DataMessage = await ws.receive_json()
    assert data_message["type"] == "data"
    assert data_message["id"] == "demo"
    assert data_message["payload"]["data"] is None

    assert "errors" in data_message["payload"]
    assert data_message["payload"]["errors"] is not None
    assert len(data_message["payload"]["errors"]) == 1

    assert "path" in data_message["payload"]["errors"][0]
    assert data_message["payload"]["errors"][0]["path"] == ["error"]

    assert "message" in data_message["payload"]["errors"][0]
    assert data_message["payload"]["errors"][0]["message"] == "TEST ERR"

    complete_message: CompleteMessage = await ws.receive_json()
    assert complete_message["type"] == "complete"
    assert complete_message["id"] == "demo"


async def test_subscription_exceptions(ws: WebSocketClient):
    await ws.send_legacy_message(
        {
            "type": "start",
            "id": "demo",
            "payload": {"query": 'subscription { exception(message: "TEST EXC") }'},
        }
    )

    data_message: DataMessage = await ws.receive_json()
    assert data_message["type"] == "data"
    assert data_message["id"] == "demo"
    assert data_message["payload"]["data"] is None

    assert "errors" in data_message["payload"]
    assert data_message["payload"]["errors"] is not None
    assert data_message["payload"]["errors"] == [{"message": "TEST EXC"}]

    await ws.send_legacy_message({"type": "stop", "id": "demo"})
    complete_message = await ws.receive_json()
    assert complete_message["type"] == "complete"
    assert complete_message["id"] == "demo"


async def test_subscription_field_error(ws: WebSocketClient):
    await ws.send_legacy_message(
        {
            "type": "start",
            "id": "invalid-field",
            "payload": {"query": "subscription { notASubscriptionField }"},
        }
    )

    error_message: ErrorMessage = await ws.receive_json()
    assert error_message["type"] == "error"
    assert error_message["id"] == "invalid-field"
    assert error_message["payload"] == {
        "locations": [{"line": 1, "column": 16}],
        "message": (
            "Cannot query field 'notASubscriptionField' on type 'Subscription'."
        ),
    }


async def test_subscription_syntax_error(ws: WebSocketClient):
    await ws.send_legacy_message(
        {
            "type": "start",
            "id": "syntax-error",
            "payload": {"query": "subscription { example "},
        }
    )

    error_message: ErrorMessage = await ws.receive_json()
    assert error_message["type"] == "error"
    assert error_message["id"] == "syntax-error"
    assert error_message["payload"] == {
        "locations": [{"line": 1, "column": 24}],
        "message": "Syntax Error: Expected Name, found <EOF>.",
    }


async def test_non_text_ws_messages_result_in_socket_closure(ws_raw: WebSocketClient):
    ws = ws_raw

    await ws.send_bytes(
        json.dumps(ConnectionInitMessage({"type": "connection_init"})).encode()
    )

    await ws.receive(timeout=2)
    assert ws.closed
    assert ws.close_code == 1002
    assert ws.close_reason == "WebSocket message type must be text"


async def test_non_json_ws_messages_are_ignored(ws_raw: WebSocketClient):
    ws = ws_raw

    await ws.send_text("NOT VALID JSON")
    await ws.send_legacy_message({"type": "connection_init"})

    connection_ack_message: ConnectionAckMessage = await ws.receive_json()
    assert connection_ack_message["type"] == "connection_ack"

    await ws.send_text("NOT VALID JSON")
    await ws.send_legacy_message(
        {
            "type": "start",
            "id": "demo",
            "payload": {
                "query": 'subscription { echo(message: "Hi") }',
            },
        }
    )

    data_message = await ws.receive_json()
    assert data_message["type"] == "data"
    assert data_message["id"] == "demo"
    assert data_message["payload"]["data"] == {"echo": "Hi"}

    await ws.send_text("NOT VALID JSON")
    await ws.send_legacy_message({"type": "stop", "id": "demo"})

    complete_message: CompleteMessage = await ws.receive_json()
    assert complete_message["type"] == "complete"
    assert complete_message["id"] == "demo"

    await ws.send_text("NOT VALID JSON")
    await ws.send_legacy_message({"type": "connection_terminate"})
    await ws.receive(timeout=2)  # receive close
    assert ws.closed


async def test_ws_message_frame_types_cannot_be_mixed(ws_raw: WebSocketClient):
    ws = ws_raw

    await ws.send_legacy_message({"type": "connection_init"})

    connection_ack_message: ConnectionAckMessage = await ws.receive_json()
    assert connection_ack_message["type"] == "connection_ack"

    await ws.send_bytes(
        json.dumps(
            StartMessage(
                {
                    "type": "start",
                    "id": "demo",
                    "payload": {
                        "query": 'subscription { echo(message: "Hi") }',
                    },
                }
            )
        ).encode()
    )

    await ws.receive(timeout=2)
    assert ws.closed
    assert ws.close_code == 1002
    assert ws.close_reason == "WebSocket message type must be text"


async def test_unknown_protocol_messages_are_ignored(ws_raw: WebSocketClient):
    ws = ws_raw
    await ws.send_json({"type": "NotAProtocolMessage"})
    await ws.send_legacy_message({"type": "connection_init"})

    await ws.send_json({"type": "NotAProtocolMessage"})
    await ws.send_legacy_message(
        {
            "type": "start",
            "id": "demo",
            "payload": {
                "query": 'subscription { echo(message: "Hi") }',
            },
        }
    )

    connection_ack_message: ConnectionAckMessage = await ws.receive_json()
    assert connection_ack_message["type"] == "connection_ack"

    data_message = await ws.receive_json()
    assert data_message["type"] == "data"
    assert data_message["id"] == "demo"
    assert data_message["payload"]["data"] == {"echo": "Hi"}

    await ws.send_json({"type": "NotAProtocolMessage"})
    await ws.send_legacy_message({"type": "stop", "id": "demo"})

    complete_message: CompleteMessage = await ws.receive_json()
    assert complete_message["type"] == "complete"
    assert complete_message["id"] == "demo"

    await ws.send_json({"type": "NotAProtocolMessage"})
    await ws.send_legacy_message({"type": "connection_terminate"})

    # make sure the WebSocket is disconnected now
    await ws.receive(timeout=2)  # receive close
    assert ws.closed


async def test_custom_context(ws: WebSocketClient):
    await ws.send_legacy_message(
        {
            "type": "start",
            "id": "demo",
            "payload": {
                "query": "subscription { context }",
            },
        }
    )

    data_message: DataMessage = await ws.receive_json()
    assert data_message["type"] == "data"
    assert data_message["id"] == "demo"
    assert data_message["payload"]["data"] == {"context": "a value from context"}

    await ws.send_legacy_message({"type": "stop", "id": "demo"})

    complete_message: CompleteMessage = await ws.receive_json()
    assert complete_message["type"] == "complete"
    assert complete_message["id"] == "demo"


async def test_resolving_enums(ws: WebSocketClient):
    await ws.send_legacy_message(
        {
            "type": "start",
            "id": "demo",
            "payload": {
                "query": "subscription { flavors }",
            },
        }
    )

    data_message1: DataMessage = await ws.receive_json()
    assert data_message1["type"] == "data"
    assert data_message1["id"] == "demo"
    assert data_message1["payload"]["data"] == {"flavors": "VANILLA"}

    data_message2: DataMessage = await ws.receive_json()
    assert data_message2["type"] == "data"
    assert data_message2["id"] == "demo"
    assert data_message2["payload"]["data"] == {"flavors": "STRAWBERRY"}

    data_message3: DataMessage = await ws.receive_json()
    assert data_message3["type"] == "data"
    assert data_message3["id"] == "demo"
    assert data_message3["payload"]["data"] == {"flavors": "CHOCOLATE"}

    await ws.send_legacy_message({"type": "stop", "id": "demo"})

    complete_message: CompleteMessage = await ws.receive_json()
    assert complete_message["type"] == "complete"
    assert complete_message["id"] == "demo"


@pytest.mark.xfail(reason="flaky test")
async def test_task_cancellation_separation(aiohttp_app_client: HttpClient):
    # Note Python 3.7 does not support Task.get_name/get_coro so we have to use
    # repr(Task) to check whether expected tasks are running.
    # This only works for aiohttp, where we are using the same event loop
    # on the client side and server.
    try:
        from tests.http.clients.aiohttp import AioHttpClient

        aio = aiohttp_app_client == AioHttpClient  # type: ignore
    except ImportError:
        aio = False

    def get_result_handler_tasks():
        return [
            task
            for task in asyncio.all_tasks()
            if "BaseGraphQLWSHandler.handle_async_results" in repr(task)
        ]

    connection1 = aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_WS_PROTOCOL]
    )
    connection2 = aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_WS_PROTOCOL]
    )

    async with connection1 as ws1, connection2 as ws2:
        start_message: StartMessage = {
            "type": "start",
            "id": "demo",
            "payload": {"query": 'subscription { infinity(message: "Hi") }'},
        }

        # 0 active result handler tasks
        if aio:
            assert len(get_result_handler_tasks()) == 0

        await ws1.send_legacy_message({"type": "connection_init"})
        await ws1.send_legacy_message(start_message)
        await ws1.receive_json()  # ack
        await ws1.receive_json()  # data

        # 1 active result handler tasks
        if aio:
            assert len(get_result_handler_tasks()) == 1

        await ws2.send_legacy_message({"type": "connection_init"})
        await ws2.send_legacy_message(start_message)
        await ws2.receive_json()
        await ws2.receive_json()

        # 2 active result handler tasks
        if aio:
            assert len(get_result_handler_tasks()) == 2

        await ws1.send_legacy_message({"type": "stop", "id": "demo"})
        await ws1.receive_json()  # complete

        # 1 active result handler tasks
        if aio:
            assert len(get_result_handler_tasks()) == 1

        await ws2.send_legacy_message({"type": "stop", "id": "demo"})
        await ws2.receive_json()  # complete

        # 0 active result handler tasks
        if aio:
            assert len(get_result_handler_tasks()) == 0

        await ws1.send_legacy_message(
            {
                "type": "start",
                "id": "debug1",
                "payload": {
                    "query": "subscription { debug { numActiveResultHandlers } }",
                },
            }
        )

        data_message: DataMessage = await ws1.receive_json()
        assert data_message["type"] == "data"
        assert data_message["id"] == "debug1"

        # The one active result handler is the one for this debug subscription
        assert data_message["payload"]["data"] == {
            "debug": {"numActiveResultHandlers": 1}
        }

        complete_message: CompleteMessage = await ws1.receive_json()
        assert complete_message["type"] == "complete"
        assert complete_message["id"] == "debug1"


async def test_injects_connection_params(aiohttp_app_client: HttpClient):
    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_WS_PROTOCOL]
    ) as ws:
        await ws.send_legacy_message(
            {
                "type": "connection_init",
                "payload": {"strawberry": "rocks"},
            }
        )
        await ws.send_legacy_message(
            {
                "type": "start",
                "id": "demo",
                "payload": {
                    "query": "subscription { connectionParams }",
                },
            }
        )

        connection_ack_message: ConnectionAckMessage = await ws.receive_json()
        assert connection_ack_message["type"] == "connection_ack"

        data_message: DataMessage = await ws.receive_json()
        assert data_message["type"] == "data"
        assert data_message["id"] == "demo"
        assert data_message["payload"]["data"] == {
            "connectionParams": {"strawberry": "rocks"}
        }

        await ws.send_legacy_message({"type": "stop", "id": "demo"})

        complete_message: CompleteMessage = await ws.receive_json()
        assert complete_message["type"] == "complete"
        assert complete_message["id"] == "demo"

        await ws.send_legacy_message({"type": "connection_terminate"})

        # make sure the WebSocket is disconnected now
        await ws.receive(timeout=2)  # receive close
        assert ws.closed


async def test_rejects_connection_params(aiohttp_app_client: HttpClient):
    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_WS_PROTOCOL]
    ) as ws:
        await ws.send_json(
            {
                "type": "connection_init",
                "id": "demo",
                "payload": "gonna fail",
            }
        )

        connection_error_message: ConnectionErrorMessage = await ws.receive_json()
        assert connection_error_message["type"] == "connection_error"

        # make sure the WebSocket is disconnected now
        await ws.receive(timeout=2)  # receive close
        assert ws.closed


@mock.patch.object(MyExtension, MyExtension.get_results.__name__, return_value={})
async def test_no_extensions_results_wont_send_extensions_in_payload(
    mock: mock.MagicMock, aiohttp_app_client: HttpClient
):
    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_WS_PROTOCOL]
    ) as ws:
        await ws.send_legacy_message({"type": "connection_init"})
        await ws.send_legacy_message(
            {
                "type": "start",
                "id": "demo",
                "payload": {
                    "query": 'subscription { echo(message: "Hi") }',
                },
            }
        )

        connection_ack_message = await ws.receive_json()
        assert connection_ack_message["type"] == "connection_ack"

        data_message: DataMessage = await ws.receive_json()
        mock.assert_called_once()
        assert data_message["type"] == "data"
        assert data_message["id"] == "demo"
        assert "extensions" not in data_message["payload"]

        await ws.send_legacy_message({"type": "stop", "id": "demo"})
        await ws.receive_json()


async def test_unexpected_client_disconnects_are_gracefully_handled(
    ws_raw: WebSocketClient,
):
    ws = ws_raw
    process_errors = mock.Mock()

    with mock.patch.object(Schema, "process_errors", process_errors):
        await ws.send_legacy_message({"type": "connection_init"})

        connection_ack_message: ConnectionAckMessage = await ws.receive_json()
        assert connection_ack_message["type"] == "connection_ack"

        await ws.send_legacy_message(
            {
                "type": "start",
                "id": "sub1",
                "payload": {
                    "query": 'subscription { echo(message: "Hi", delay: 0.5) }',
                },
            }
        )

        await ws.close()
        await asyncio.sleep(1)
        assert not process_errors.called
