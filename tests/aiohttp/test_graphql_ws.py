import asyncio

from aiohttp import web
from strawberry.aiohttp.views import GraphQLView
from strawberry.subscriptions import GRAPHQL_WS_PROTOCOL
from strawberry.subscriptions.protocols.graphql_ws import (
    GQL_COMPLETE,
    GQL_CONNECTION_ACK,
    GQL_CONNECTION_INIT,
    GQL_CONNECTION_KEEP_ALIVE,
    GQL_CONNECTION_TERMINATE,
    GQL_DATA,
    GQL_ERROR,
    GQL_START,
    GQL_STOP,
)
from tests.aiohttp.app import create_app
from tests.aiohttp.schema import schema


async def test_simple_subscription(aiohttp_client):
    app = create_app(keep_alive=False)
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_WS_PROTOCOL]
    ) as ws:
        await ws.send_json({"type": GQL_CONNECTION_INIT})
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

        await ws.send_json({"type": GQL_STOP, "id": "demo"})
        response = await ws.receive_json()
        assert response["type"] == GQL_COMPLETE
        assert response["id"] == "demo"

        await ws.send_json({"type": GQL_CONNECTION_TERMINATE})

        # make sure the WebSocket is disconnected now
        await ws.receive(timeout=2)  # receive close
        assert ws.closed


async def test_operation_selection(aiohttp_client):
    app = create_app(keep_alive=False)
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_WS_PROTOCOL]
    ) as ws:
        await ws.send_json({"type": GQL_CONNECTION_INIT})
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
        assert response["type"] == GQL_CONNECTION_ACK

        response = await ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "demo"
        assert response["payload"]["data"] == {"echo": "Hi2"}

        await ws.send_json({"type": GQL_STOP, "id": "demo"})
        response = await ws.receive_json()
        assert response["type"] == GQL_COMPLETE
        assert response["id"] == "demo"

        await ws.send_json({"type": GQL_CONNECTION_TERMINATE})

        # make sure the WebSocket is disconnected now
        await ws.receive(timeout=2)  # receive close
        assert ws.closed


async def test_sends_keep_alive(aiohttp_client, event_loop):
    app = create_app(keep_alive=True, keep_alive_interval=0.1)
    aiohttp_app_client = await aiohttp_client(app)

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

        response = await ws.receive_json()
        assert response["type"] == GQL_CONNECTION_KEEP_ALIVE

        response = await ws.receive_json()
        assert response["type"] == GQL_CONNECTION_KEEP_ALIVE

        response = await ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "demo"
        assert response["payload"]["data"] == {"echo": "Hi"}

        response = await ws.receive_json()
        assert response["type"] == GQL_COMPLETE
        assert response["id"] == "demo"

        await ws.send_json({"type": GQL_CONNECTION_TERMINATE})


async def test_subscription_cancellation(aiohttp_client):
    app = create_app(keep_alive=False)
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_WS_PROTOCOL]
    ) as ws:
        await ws.send_json({"type": GQL_CONNECTION_INIT})
        response = await ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK

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

        await ws.send_json({"type": GQL_CONNECTION_TERMINATE})

        # make sure the WebSocket is disconnected now
        await ws.receive(timeout=2)  # receive close
        assert ws.closed


async def test_subscription_errors(aiohttp_client):
    app = create_app(keep_alive=False)
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_WS_PROTOCOL]
    ) as ws:
        await ws.send_json({"type": GQL_CONNECTION_INIT})
        await ws.send_json(
            {
                "type": GQL_START,
                "id": "demo",
                "payload": {"query": 'subscription { error(message: "TEST ERR") }'},
            }
        )

        response = await ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK

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

        await ws.send_json({"type": GQL_CONNECTION_TERMINATE})


async def test_subscription_exceptions(aiohttp_client):
    app = create_app(keep_alive=False)
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_WS_PROTOCOL]
    ) as ws:
        await ws.send_json({"type": GQL_CONNECTION_INIT})
        await ws.send_json(
            {
                "type": GQL_START,
                "id": "demo",
                "payload": {"query": 'subscription { exception(message: "TEST EXC") }'},
            }
        )

        response = await ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK

        response = await ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "demo"
        assert response["payload"]["data"] is None
        assert response["payload"]["errors"] == [{"message": "TEST EXC"}]

        await ws.send_json({"type": GQL_STOP, "id": "demo"})
        response = await ws.receive_json()
        assert response["type"] == GQL_COMPLETE
        assert response["id"] == "demo"

        await ws.send_json({"type": GQL_CONNECTION_TERMINATE})

        # make sure the WebSocket is disconnected now
        await ws.receive(timeout=2)  # receive close
        assert ws.closed


async def test_subscription_field_error(aiohttp_client):
    app = create_app(keep_alive=False)
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_WS_PROTOCOL]
    ) as ws:
        await ws.send_json({"type": GQL_CONNECTION_INIT})
        await ws.send_json(
            {
                "type": GQL_START,
                "id": "invalid-field",
                "payload": {"query": "subscription { notASubscriptionField }"},
            }
        )

        response = await ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK

        response = await ws.receive_json()
        assert response["type"] == GQL_ERROR
        assert response["id"] == "invalid-field"
        assert response["payload"] == {
            "locations": [{"line": 1, "column": 16}],
            "message": (
                "The subscription field 'notASubscriptionField' is not defined."
            ),
        }

        await ws.send_json({"type": GQL_CONNECTION_TERMINATE})

        # make sure the WebSocket is disconnected now
        await ws.receive(timeout=2)  # receive close
        assert ws.closed


async def test_subscription_syntax_error(aiohttp_client):
    app = create_app(keep_alive=False)
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_WS_PROTOCOL]
    ) as ws:
        await ws.send_json({"type": GQL_CONNECTION_INIT})
        await ws.send_json(
            {
                "type": GQL_START,
                "id": "syntax-error",
                "payload": {"query": "subscription { example "},
            }
        )

        response = await ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK

        response = await ws.receive_json()
        assert response["type"] == GQL_ERROR
        assert response["id"] == "syntax-error"
        assert response["payload"] == {
            "locations": [{"line": 1, "column": 24}],
            "message": "Syntax Error: Expected Name, found <EOF>.",
        }

        await ws.send_json({"type": GQL_CONNECTION_TERMINATE})

        # make sure the WebSocket is disconnected now
        await ws.receive(timeout=2)  # receive close
        assert ws.closed


async def test_non_text_ws_messages_are_ignored(aiohttp_client):
    app = create_app(keep_alive=False)
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_WS_PROTOCOL]
    ) as ws:
        await ws.send_bytes(b"")
        await ws.send_json({"type": GQL_CONNECTION_INIT})

        await ws.send_bytes(b"")
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

        await ws.send_bytes(b"")
        await ws.send_json({"type": GQL_STOP, "id": "demo"})
        response = await ws.receive_json()
        assert response["type"] == GQL_COMPLETE
        assert response["id"] == "demo"

        await ws.send_bytes(b"")
        await ws.send_json({"type": GQL_CONNECTION_TERMINATE})

        # make sure the WebSocket is disconnected now
        await ws.receive(timeout=2)  # receive close
        assert ws.closed


async def test_unknown_protocol_messages_are_ignored(aiohttp_client):
    app = create_app(keep_alive=False)
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_WS_PROTOCOL]
    ) as ws:
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


async def test_custom_context(aiohttp_client):
    class MyGraphQLView(GraphQLView):
        async def get_context(self, request, response) -> object:
            return {"request": request, "response": response, "custom_value": "Hi"}

    view = MyGraphQLView(schema=schema, keep_alive=False)
    app = web.Application()
    app.router.add_route("*", "/graphql", view)
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_WS_PROTOCOL]
    ) as ws:
        await ws.send_json({"type": GQL_CONNECTION_INIT})
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
        assert response["type"] == GQL_CONNECTION_ACK

        response = await ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "demo"
        assert response["payload"]["data"] == {"context": "Hi"}

        await ws.send_json({"type": GQL_STOP, "id": "demo"})
        response = await ws.receive_json()
        assert response["type"] == GQL_COMPLETE
        assert response["id"] == "demo"

        await ws.send_json({"type": GQL_CONNECTION_TERMINATE})

        # make sure the WebSocket is disconnected now
        await ws.receive(timeout=2)  # receive close
        assert ws.closed


async def test_resolving_enums(aiohttp_client):
    app = create_app(keep_alive=False)
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_WS_PROTOCOL]
    ) as ws:
        await ws.send_json({"type": GQL_CONNECTION_INIT})
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
        assert response["type"] == GQL_CONNECTION_ACK

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

        await ws.send_json({"type": GQL_CONNECTION_TERMINATE})

        # make sure the WebSocket is disconnected now
        await ws.receive(timeout=2)  # receive close
        assert ws.closed


async def test_task_cancellation_separation(aiohttp_client):
    view = GraphQLView(schema=schema, keep_alive=False)
    app = web.Application()
    app.router.add_route("*", "/graphql", view)
    aiohttp_app_client = await aiohttp_client(app)

    # Note Python 3.7 does not support Task.get_name/get_coro so we have to use
    # repr(Task) to check whether expected tasks are running.
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

        assert len(get_result_handler_tasks()) == 0

        await ws1.send_json({"type": GQL_CONNECTION_INIT})
        await ws1.send_json(start_payload)
        await ws1.receive_json()

        assert len(get_result_handler_tasks()) == 1

        await ws2.send_json({"type": GQL_CONNECTION_INIT})
        await ws2.send_json(start_payload)
        await ws2.receive_json()

        assert len(get_result_handler_tasks()) == 2

        await ws1.send_json({"type": GQL_STOP, "id": "demo"})
        await ws1.send_json({"type": GQL_CONNECTION_TERMINATE})

        async for msg in ws1:
            # Receive all outstanding messages including the final close message
            pass

        assert len(get_result_handler_tasks()) == 1

        await ws2.send_json({"type": GQL_STOP, "id": "demo"})
        await ws2.send_json({"type": GQL_CONNECTION_TERMINATE})

        async for msg in ws2:
            # Receive all outstanding messages including the final close message
            pass

        assert len(get_result_handler_tasks()) == 0
