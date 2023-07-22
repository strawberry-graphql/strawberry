from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, AsyncGenerator

import pytest
import pytest_asyncio

from strawberry.subscriptions import GRAPHQL_WS_PROTOCOL
from strawberry.subscriptions.protocols.graphql_ws import (
    GQL_COMPLETE,
    GQL_CONNECTION_ACK,
    GQL_CONNECTION_ERROR,
    GQL_CONNECTION_INIT,
    GQL_CONNECTION_KEEP_ALIVE,
    GQL_CONNECTION_TERMINATE,
    GQL_DATA,
    GQL_ERROR,
    GQL_START,
    GQL_STOP,
)

if TYPE_CHECKING:
    from ..http.clients.aiohttp import HttpClient, WebSocketClient


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
    await ws.send_json({"type": GQL_CONNECTION_INIT})
    response = await ws.receive_json()
    assert response["type"] == GQL_CONNECTION_ACK

    yield ws

    await ws.send_json({"type": GQL_CONNECTION_TERMINATE})
    # make sure the WebSocket is disconnected now
    await ws.receive(timeout=2)  # receive close
    assert ws.closed


# convenience fixture to use previous name
@pytest.fixture
def aiohttp_app_client(http_client: HttpClient) -> HttpClient:
    return http_client


async def test_simple_subscription(ws: WebSocketClient):
    await ws.send_json(
        {
            "type": GQL_START,
            "id": "demo",
            "payload": {
                "query": 'subscription { echo(message: "Hi") }',
            },
        }
    )

    response = await ws.receive_json()
    assert response["type"] == GQL_DATA
    assert response["id"] == "demo"
    assert response["payload"]["data"] == {"echo": "Hi"}

    await ws.send_json({"type": GQL_STOP, "id": "demo"})
    response = await ws.receive_json()
    assert response["type"] == GQL_COMPLETE
    assert response["id"] == "demo"


async def test_operation_selection(ws: WebSocketClient):
    await ws.send_json(
        {
            "type": GQL_START,
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

    response = await ws.receive_json()
    assert response["type"] == GQL_DATA
    assert response["id"] == "demo"
    assert response["payload"]["data"] == {"echo": "Hi2"}

    await ws.send_json({"type": GQL_STOP, "id": "demo"})
    response = await ws.receive_json()
    assert response["type"] == GQL_COMPLETE
    assert response["id"] == "demo"


async def test_sends_keep_alive(aiohttp_app_client: HttpClient):
    aiohttp_app_client.create_app(keep_alive=True, keep_alive_interval=0.1)
    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_WS_PROTOCOL]
    ) as ws:
        await ws.send_json({"type": GQL_CONNECTION_INIT})
        await ws.send_json(
            {
                "type": GQL_START,
                "id": "demo",
                "payload": {
                    "query": 'subscription { echo(message: "Hi", delay: 0.15) }',
                },
            }
        )

        response = await ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK

        # we can't be sure how many keep-alives exactly we
        # get but they should be more than one.
        keepalive_count = 0
        while True:
            response = await ws.receive_json()
            if response["type"] == GQL_CONNECTION_KEEP_ALIVE:
                keepalive_count += 1
            else:
                break
        assert keepalive_count >= 1

        assert response["type"] == GQL_DATA
        assert response["id"] == "demo"
        assert response["payload"]["data"] == {"echo": "Hi"}

        response = await ws.receive_json()
        assert response["type"] == GQL_COMPLETE
        assert response["id"] == "demo"

        await ws.send_json({"type": GQL_CONNECTION_TERMINATE})


async def test_subscription_cancellation(ws: WebSocketClient):
    await ws.send_json(
        {
            "type": GQL_START,
            "id": "demo",
            "payload": {"query": 'subscription { echo(message: "Hi", delay: 99) }'},
        }
    )

    await ws.send_json(
        {
            "type": GQL_START,
            "id": "debug1",
            "payload": {
                "query": "subscription { debug { numActiveResultHandlers } }",
            },
        }
    )

    response = await ws.receive_json()
    assert response["type"] == GQL_DATA
    assert response["id"] == "debug1"
    assert response["payload"]["data"] == {"debug": {"numActiveResultHandlers": 2}}

    response = await ws.receive_json()
    assert response["type"] == GQL_COMPLETE
    assert response["id"] == "debug1"

    await ws.send_json({"type": GQL_STOP, "id": "demo"})
    response = await ws.receive_json()
    assert response["type"] == GQL_COMPLETE
    assert response["id"] == "demo"

    await ws.send_json(
        {
            "type": GQL_START,
            "id": "debug2",
            "payload": {
                "query": "subscription { debug { numActiveResultHandlers} }",
            },
        }
    )

    response = await ws.receive_json()
    assert response["type"] == GQL_DATA
    assert response["id"] == "debug2"
    assert response["payload"]["data"] == {"debug": {"numActiveResultHandlers": 1}}

    response = await ws.receive_json()
    assert response["type"] == GQL_COMPLETE
    assert response["id"] == "debug2"


async def test_subscription_errors(ws: WebSocketClient):
    await ws.send_json(
        {
            "type": GQL_START,
            "id": "demo",
            "payload": {"query": 'subscription { error(message: "TEST ERR") }'},
        }
    )

    response = await ws.receive_json()
    assert response["type"] == GQL_DATA
    assert response["id"] == "demo"
    assert response["payload"]["data"] is None
    assert len(response["payload"]["errors"]) == 1
    assert response["payload"]["errors"][0]["path"] == ["error"]
    assert response["payload"]["errors"][0]["message"] == "TEST ERR"

    response = await ws.receive_json()
    assert response["type"] == GQL_COMPLETE
    assert response["id"] == "demo"


async def test_subscription_exceptions(ws: WebSocketClient):
    await ws.send_json(
        {
            "type": GQL_START,
            "id": "demo",
            "payload": {"query": 'subscription { exception(message: "TEST EXC") }'},
        }
    )

    response = await ws.receive_json()
    assert response["type"] == GQL_DATA
    assert response["id"] == "demo"
    assert response["payload"]["data"] is None
    assert response["payload"]["errors"] == [{"message": "TEST EXC"}]

    await ws.send_json({"type": GQL_STOP, "id": "demo"})
    response = await ws.receive_json()
    assert response["type"] == GQL_COMPLETE
    assert response["id"] == "demo"


async def test_subscription_field_error(ws: WebSocketClient):
    await ws.send_json(
        {
            "type": GQL_START,
            "id": "invalid-field",
            "payload": {"query": "subscription { notASubscriptionField }"},
        }
    )

    response = await ws.receive_json()
    assert response["type"] == GQL_ERROR
    assert response["id"] == "invalid-field"
    assert response["payload"] == {
        "locations": [{"line": 1, "column": 16}],
        "message": ("The subscription field 'notASubscriptionField' is not defined."),
    }


async def test_subscription_syntax_error(ws: WebSocketClient):
    await ws.send_json(
        {
            "type": GQL_START,
            "id": "syntax-error",
            "payload": {"query": "subscription { example "},
        }
    )

    response = await ws.receive_json()
    assert response["type"] == GQL_ERROR
    assert response["id"] == "syntax-error"
    assert response["payload"] == {
        "locations": [{"line": 1, "column": 24}],
        "message": "Syntax Error: Expected Name, found <EOF>.",
    }


async def test_non_text_ws_messages_are_ignored(ws_raw: WebSocketClient):
    ws = ws_raw
    await ws.send_bytes(b"foo")
    await ws.send_json({"type": GQL_CONNECTION_INIT})

    await ws.send_bytes(b"bar")
    await ws.send_json(
        {
            "type": GQL_START,
            "id": "demo",
            "payload": {
                "query": 'subscription { echo(message: "Hi") }',
            },
        }
    )

    response = await ws.receive_json()
    assert response["type"] == GQL_CONNECTION_ACK

    response = await ws.receive_json()
    assert response["type"] == GQL_DATA
    assert response["id"] == "demo"
    assert response["payload"]["data"] == {"echo": "Hi"}

    await ws.send_bytes(b"gaz")
    await ws.send_json({"type": GQL_STOP, "id": "demo"})
    response = await ws.receive_json()
    assert response["type"] == GQL_COMPLETE
    assert response["id"] == "demo"

    await ws.send_bytes(b"wat")
    await ws.send_json({"type": GQL_CONNECTION_TERMINATE})

    # make sure the WebSocket is disconnected now
    await ws.receive(timeout=2)  # receive close
    assert ws.closed


async def test_unknown_protocol_messages_are_ignored(ws_raw: WebSocketClient):
    ws = ws_raw
    await ws.send_json({"type": "NotAProtocolMessage"})
    await ws.send_json({"type": GQL_CONNECTION_INIT})

    await ws.send_json({"type": "NotAProtocolMessage"})
    await ws.send_json(
        {
            "type": GQL_START,
            "id": "demo",
            "payload": {
                "query": 'subscription { echo(message: "Hi") }',
            },
        }
    )

    response = await ws.receive_json()
    assert response["type"] == GQL_CONNECTION_ACK

    response = await ws.receive_json()
    assert response["type"] == GQL_DATA
    assert response["id"] == "demo"
    assert response["payload"]["data"] == {"echo": "Hi"}

    await ws.send_json({"type": "NotAProtocolMessage"})
    await ws.send_json({"type": GQL_STOP, "id": "demo"})
    response = await ws.receive_json()
    assert response["type"] == GQL_COMPLETE
    assert response["id"] == "demo"

    await ws.send_json({"type": "NotAProtocolMessage"})
    await ws.send_json({"type": GQL_CONNECTION_TERMINATE})

    # make sure the WebSocket is disconnected now
    await ws.receive(timeout=2)  # receive close
    assert ws.closed


async def test_custom_context(ws: WebSocketClient):
    await ws.send_json(
        {
            "type": GQL_START,
            "id": "demo",
            "payload": {
                "query": "subscription { context }",
            },
        }
    )

    response = await ws.receive_json()
    assert response["type"] == GQL_DATA
    assert response["id"] == "demo"
    assert response["payload"]["data"] == {"context": "a value from context"}

    await ws.send_json({"type": GQL_STOP, "id": "demo"})
    response = await ws.receive_json()
    assert response["type"] == GQL_COMPLETE
    assert response["id"] == "demo"


async def test_resolving_enums(ws: WebSocketClient):
    await ws.send_json(
        {
            "type": GQL_START,
            "id": "demo",
            "payload": {
                "query": "subscription { flavors }",
            },
        }
    )

    response = await ws.receive_json()
    assert response["type"] == GQL_DATA
    assert response["id"] == "demo"
    assert response["payload"]["data"] == {"flavors": "VANILLA"}

    response = await ws.receive_json()
    assert response["type"] == GQL_DATA
    assert response["id"] == "demo"
    assert response["payload"]["data"] == {"flavors": "STRAWBERRY"}

    response = await ws.receive_json()
    assert response["type"] == GQL_DATA
    assert response["id"] == "demo"
    assert response["payload"]["data"] == {"flavors": "CHOCOLATE"}

    await ws.send_json({"type": GQL_STOP, "id": "demo"})
    response = await ws.receive_json()
    assert response["type"] == GQL_COMPLETE
    assert response["id"] == "demo"


async def test_task_cancellation_separation(aiohttp_app_client: HttpClient):
    # Note Python 3.7 does not support Task.get_name/get_coro so we have to use
    # repr(Task) to check whether expected tasks are running.
    # This only works for aiohttp, where we are using the same event loop
    # on the client side and server.
    try:
        from ..http.clients.aiohttp import AioHttpClient

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
        start_payload = {
            "type": GQL_START,
            "id": "demo",
            "payload": {"query": 'subscription { infinity(message: "Hi") }'},
        }

        # 0 active result handler tasks
        if aio:
            assert len(get_result_handler_tasks()) == 0

        await ws1.send_json({"type": GQL_CONNECTION_INIT})
        await ws1.send_json(start_payload)
        await ws1.receive_json()  # ack
        await ws1.receive_json()  # data

        # 1 active result handler tasks
        if aio:
            assert len(get_result_handler_tasks()) == 1

        await ws2.send_json({"type": GQL_CONNECTION_INIT})
        await ws2.send_json(start_payload)
        await ws2.receive_json()
        await ws2.receive_json()

        # 2 active result handler tasks
        if aio:
            assert len(get_result_handler_tasks()) == 2

        await ws1.send_json({"type": GQL_STOP, "id": "demo"})
        await ws1.receive_json()  # complete

        # 1 active result handler tasks
        if aio:
            assert len(get_result_handler_tasks()) == 1

        await ws2.send_json({"type": GQL_STOP, "id": "demo"})
        await ws2.receive_json()  # complete

        # 0 active result handler tasks
        if aio:
            assert len(get_result_handler_tasks()) == 0

        await ws1.send_json(
            {
                "type": GQL_START,
                "id": "debug1",
                "payload": {
                    "query": "subscription { debug { numActiveResultHandlers } }",
                },
            }
        )

        response = await ws1.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "debug1"

        # The one active result handler is the one for this debug subscription
        assert response["payload"]["data"] == {"debug": {"numActiveResultHandlers": 1}}

        response = await ws1.receive_json()
        assert response["type"] == GQL_COMPLETE
        assert response["id"] == "debug1"


async def test_injects_connection_params(aiohttp_app_client: HttpClient):
    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_WS_PROTOCOL]
    ) as ws:
        await ws.send_json(
            {
                "type": GQL_CONNECTION_INIT,
                "id": "demo",
                "payload": {"strawberry": "rocks"},
            }
        )
        await ws.send_json(
            {
                "type": GQL_START,
                "id": "demo",
                "payload": {
                    "query": "subscription { connectionParams }",
                },
            }
        )

        response = await ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK

        response = await ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "demo"
        assert response["payload"]["data"] == {"connectionParams": "rocks"}

        await ws.send_json({"type": GQL_STOP, "id": "demo"})
        response = await ws.receive_json()
        assert response["type"] == GQL_COMPLETE
        assert response["id"] == "demo"

        await ws.send_json({"type": GQL_CONNECTION_TERMINATE})

        # make sure the WebSocket is disconnected now
        await ws.receive(timeout=2)  # receive close
        assert ws.closed


async def test_rejects_connection_params(aiohttp_app_client: HttpClient):
    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_WS_PROTOCOL]
    ) as ws:
        await ws.send_json(
            {
                "type": GQL_CONNECTION_INIT,
                "id": "demo",
                "payload": "gonna fail",
            }
        )

        response = await ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ERROR

        # make sure the WebSocket is disconnected now
        await ws.receive(timeout=2)  # receive close
        assert ws.closed
