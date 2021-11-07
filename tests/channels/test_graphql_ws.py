import pytest

from channels.testing import WebsocketCommunicator
from strawberry.channels import GraphQLWSConsumer
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
from tests.channels.schema import schema


pytestmark = [
    pytest.mark.asyncio,
]


class DebuggableGraphQLWSConsumer(GraphQLWSConsumer):
    async def get_context(self, *args, **kwargs) -> object:
        context = await super().get_context(*args, **kwargs)
        context.tasks = self._handler.tasks
        context.connectionInitTimeoutTask = None
        return context


@pytest.fixture
async def ws():
    client = WebsocketCommunicator(
        DebuggableGraphQLWSConsumer.as_asgi(
            schema=schema, subscription_protocols=(GRAPHQL_WS_PROTOCOL,)
        ),
        "/graphql",
        subprotocols=[
            GRAPHQL_WS_PROTOCOL,
        ],
    )
    res = await client.connect()
    assert res == (True, GRAPHQL_WS_PROTOCOL)

    yield client

    await client.disconnect()


async def test_simple_subscription(ws):
    await ws.send_json_to({"type": GQL_CONNECTION_INIT})
    await ws.send_json_to(
        {
            "type": GQL_START,
            "id": "demo",
            "payload": {
                "query": 'subscription { echo(message: "Hi") }',
            },
        }
    )

    response = await ws.receive_json_from()
    assert response["type"] == GQL_CONNECTION_ACK

    response = await ws.receive_json_from()
    assert response["type"] == GQL_DATA
    assert response["id"] == "demo"
    assert response["payload"]["data"] == {"echo": "Hi"}

    await ws.send_json_to({"type": GQL_STOP, "id": "demo"})
    response = await ws.receive_json_from()
    assert response["type"] == GQL_COMPLETE
    assert response["id"] == "demo"

    await ws.send_json_to({"type": GQL_CONNECTION_TERMINATE})

    # make sure the websocket is disconnected now
    data = await ws.receive_output()
    assert data == {"type": "websocket.close", "code": 1000}


async def test_operation_selection(ws):
    await ws.send_json_to({"type": GQL_CONNECTION_INIT})
    await ws.send_json_to(
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

    response = await ws.receive_json_from()
    assert response["type"] == GQL_CONNECTION_ACK

    response = await ws.receive_json_from()
    assert response["type"] == GQL_DATA
    assert response["id"] == "demo"
    assert response["payload"]["data"] == {"echo": "Hi2"}

    await ws.send_json_to({"type": GQL_STOP, "id": "demo"})
    response = await ws.receive_json_from()
    assert response["type"] == GQL_COMPLETE
    assert response["id"] == "demo"

    await ws.send_json_to({"type": GQL_CONNECTION_TERMINATE})

    # make sure the websocket is disconnected now
    data = await ws.receive_output()
    assert data == {"type": "websocket.close", "code": 1000}


async def test_sends_keep_alive():
    client = WebsocketCommunicator(
        DebuggableGraphQLWSConsumer.as_asgi(
            schema=schema,
            keep_alive=True,
            keep_alive_interval=0.1,
            subscription_protocols=(GRAPHQL_WS_PROTOCOL,),
        ),
        "/graphql",
        subprotocols=[
            GRAPHQL_WS_PROTOCOL,
        ],
    )
    res = await client.connect()
    assert res == (True, GRAPHQL_WS_PROTOCOL)
    await client.send_json_to({"type": GQL_CONNECTION_INIT})
    await client.send_json_to(
        {
            "type": GQL_START,
            "id": "demo",
            "payload": {"query": 'subscription { echo(message: "Hi", delay: 0.15) }'},
        }
    )

    response = await client.receive_json_from()
    assert response["type"] == GQL_CONNECTION_ACK

    response = await client.receive_json_from()
    assert response["type"] == GQL_CONNECTION_KEEP_ALIVE

    response = await client.receive_json_from()
    assert response["type"] == GQL_CONNECTION_KEEP_ALIVE

    response = await client.receive_json_from()
    assert response["type"] == GQL_DATA
    assert response["id"] == "demo"
    assert response["payload"]["data"] == {"echo": "Hi"}

    response = await client.receive_json_from()
    assert response["type"] == GQL_COMPLETE
    assert response["id"] == "demo"

    await client.send_json_to({"type": GQL_CONNECTION_TERMINATE})


async def test_subscription_cancellation(ws):
    await ws.send_json_to({"type": GQL_CONNECTION_INIT})
    response = await ws.receive_json_from()
    assert response["type"] == GQL_CONNECTION_ACK

    await ws.send_json_to(
        {
            "type": GQL_START,
            "id": "demo",
            "payload": {"query": 'subscription { echo(message: "Hi", delay: 99) }'},
        }
    )

    await ws.send_json_to(
        {
            "type": GQL_START,
            "id": "debug1",
            "payload": {
                "query": "subscription { debug { numActiveResultHandlers } }",
            },
        }
    )

    response = await ws.receive_json_from()
    assert response["type"] == GQL_DATA
    assert response["id"] == "debug1"
    assert response["payload"]["data"] == {"debug": {"numActiveResultHandlers": 2}}

    response = await ws.receive_json_from()
    assert response["type"] == GQL_COMPLETE
    assert response["id"] == "debug1"

    await ws.send_json_to({"type": GQL_STOP, "id": "demo"})
    response = await ws.receive_json_from()
    assert response["type"] == GQL_COMPLETE
    assert response["id"] == "demo"

    await ws.send_json_to(
        {
            "type": GQL_START,
            "id": "debug2",
            "payload": {
                "query": "subscription { debug { numActiveResultHandlers} }",
            },
        }
    )

    response = await ws.receive_json_from()
    assert response["type"] == GQL_DATA
    assert response["id"] == "debug2"
    assert response["payload"]["data"] == {"debug": {"numActiveResultHandlers": 1}}

    response = await ws.receive_json_from()
    assert response["type"] == GQL_COMPLETE
    assert response["id"] == "debug2"

    await ws.send_json_to({"type": GQL_CONNECTION_TERMINATE})

    # make sure the websocket is disconnected now
    data = await ws.receive_output()
    assert data == {"type": "websocket.close", "code": 1000}


async def test_subscription_errors(ws):
    await ws.send_json_to({"type": GQL_CONNECTION_INIT})
    await ws.send_json_to(
        {
            "type": GQL_START,
            "id": "demo",
            "payload": {"query": 'subscription { error(message: "TEST ERR") }'},
        }
    )

    response = await ws.receive_json_from()
    assert response["type"] == GQL_CONNECTION_ACK

    response = await ws.receive_json_from()
    assert response["type"] == GQL_DATA
    assert response["id"] == "demo"
    assert response["payload"]["data"] is None
    assert response["payload"]["errors"][0]["path"] == ["error"]
    assert response["payload"]["errors"][0]["message"] == "TEST ERR"

    response = await ws.receive_json_from()
    assert response["type"] == GQL_COMPLETE
    assert response["id"] == "demo"

    await ws.send_json_to({"type": GQL_CONNECTION_TERMINATE})

    # make sure the websocket is disconnected now
    data = await ws.receive_output()
    assert data == {"type": "websocket.close", "code": 1000}


async def test_subscription_exceptions(ws):
    await ws.send_json_to({"type": GQL_CONNECTION_INIT})
    await ws.send_json_to(
        {
            "type": GQL_START,
            "id": "demo",
            "payload": {"query": 'subscription { exception(message: "TEST EXC") }'},
        }
    )

    response = await ws.receive_json_from()
    assert response["type"] == GQL_CONNECTION_ACK

    response = await ws.receive_json_from()
    assert response["type"] == GQL_DATA
    assert response["id"] == "demo"
    assert response["payload"]["data"] is None
    assert response["payload"]["errors"] == [
        {"locations": None, "message": "TEST EXC", "path": None}
    ]

    await ws.send_json_to({"type": GQL_STOP, "id": "demo"})
    response = await ws.receive_json_from()
    assert response["type"] == GQL_COMPLETE
    assert response["id"] == "demo"

    await ws.send_json_to({"type": GQL_CONNECTION_TERMINATE})

    # make sure the websocket is disconnected now
    data = await ws.receive_output()
    assert data == {"type": "websocket.close", "code": 1000}


async def test_subscription_field_error(ws):
    await ws.send_json_to({"type": GQL_CONNECTION_INIT})
    await ws.send_json_to(
        {
            "type": GQL_START,
            "id": "invalid-field",
            "payload": {"query": "subscription { notASubscriptionField }"},
        }
    )

    response = await ws.receive_json_from()
    assert response["type"] == GQL_CONNECTION_ACK

    response = await ws.receive_json_from()
    assert response["type"] == GQL_ERROR
    assert response["id"] == "invalid-field"
    assert response["payload"] == {
        "locations": [{"line": 1, "column": 16}],
        "path": None,
        "message": ("The subscription field 'notASubscriptionField' is not defined."),
    }

    await ws.send_json_to({"type": GQL_CONNECTION_TERMINATE})

    # make sure the websocket is disconnected now
    data = await ws.receive_output()
    assert data == {"type": "websocket.close", "code": 1000}


async def test_subscription_syntax_error(ws):
    await ws.send_json_to({"type": GQL_CONNECTION_INIT})
    await ws.send_json_to(
        {
            "type": GQL_START,
            "id": "syntax-error",
            "payload": {"query": "subscription { example "},
        }
    )

    response = await ws.receive_json_from()
    assert response["type"] == GQL_CONNECTION_ACK

    response = await ws.receive_json_from()
    assert response["type"] == GQL_ERROR
    assert response["id"] == "syntax-error"
    assert response["payload"] == {
        "locations": [{"line": 1, "column": 24}],
        "path": None,
        "message": "Syntax Error: Expected Name, found <EOF>.",
    }

    await ws.send_json_to({"type": GQL_CONNECTION_TERMINATE})

    # make sure the websocket is disconnected now
    data = await ws.receive_output()
    assert data == {"type": "websocket.close", "code": 1000}


async def test_non_text_ws_messages_are_ignored(ws):
    ws.send_to(bytes_data=b"")
    await ws.send_json_to({"type": GQL_CONNECTION_INIT})

    ws.send_to(bytes_data=b"")
    await ws.send_json_to(
        {
            "type": GQL_START,
            "id": "demo",
            "payload": {
                "query": 'subscription { echo(message: "Hi") }',
            },
        }
    )

    response = await ws.receive_json_from()
    assert response["type"] == GQL_CONNECTION_ACK

    response = await ws.receive_json_from()
    assert response["type"] == GQL_DATA
    assert response["id"] == "demo"
    assert response["payload"]["data"] == {"echo": "Hi"}

    ws.send_to(bytes_data=b"")
    await ws.send_json_to({"type": GQL_STOP, "id": "demo"})
    response = await ws.receive_json_from()
    assert response["type"] == GQL_COMPLETE
    assert response["id"] == "demo"

    ws.send_to(bytes_data=b"")
    await ws.send_json_to({"type": GQL_CONNECTION_TERMINATE})

    # make sure the websocket is disconnected now
    data = await ws.receive_output()
    assert data == {"type": "websocket.close", "code": 1000}


async def test_unknown_protocol_messages_are_ignored(ws):
    await ws.send_json_to({"type": "NotAProtocolMessage"})
    await ws.send_json_to({"type": GQL_CONNECTION_INIT})

    await ws.send_json_to({"type": "NotAProtocolMessage"})
    await ws.send_json_to(
        {
            "type": GQL_START,
            "id": "demo",
            "payload": {
                "query": 'subscription { echo(message: "Hi") }',
            },
        }
    )

    response = await ws.receive_json_from()
    assert response["type"] == GQL_CONNECTION_ACK

    response = await ws.receive_json_from()
    assert response["type"] == GQL_DATA
    assert response["id"] == "demo"
    assert response["payload"]["data"] == {"echo": "Hi"}

    await ws.send_json_to({"type": "NotAProtocolMessage"})
    await ws.send_json_to({"type": GQL_STOP, "id": "demo"})
    response = await ws.receive_json_from()
    assert response["type"] == GQL_COMPLETE
    assert response["id"] == "demo"

    await ws.send_json_to({"type": "NotAProtocolMessage"})
    await ws.send_json_to({"type": GQL_CONNECTION_TERMINATE})

    # make sure the websocket is disconnected now
    data = await ws.receive_output()
    assert data == {"type": "websocket.close", "code": 1000}


async def test_custom_context():
    class CustomDebuggableGraphQLWSConsumer(DebuggableGraphQLWSConsumer):
        async def get_context(self, *args, **kwargs) -> object:
            context = await super().get_context(*args, **kwargs)
            context.custom_value = "Hi!"
            return context

    client = WebsocketCommunicator(
        CustomDebuggableGraphQLWSConsumer.as_asgi(
            schema=schema, subscription_protocols=(GRAPHQL_WS_PROTOCOL,)
        ),
        "/graphql",
        subprotocols=[
            GRAPHQL_WS_PROTOCOL,
        ],
    )
    res = await client.connect()
    assert res == (True, GRAPHQL_WS_PROTOCOL)
    await client.send_json_to({"type": GQL_CONNECTION_INIT})
    await client.send_json_to(
        {
            "type": GQL_START,
            "id": "demo",
            "payload": {
                "query": "subscription { context }",
            },
        }
    )

    response = await client.receive_json_from()
    assert response["type"] == GQL_CONNECTION_ACK

    response = await client.receive_json_from()
    assert response["type"] == GQL_DATA
    assert response["id"] == "demo"
    assert response["payload"]["data"] == {"context": "Hi!"}

    await client.send_json_to({"type": GQL_STOP, "id": "demo"})
    response = await client.receive_json_from()
    assert response["type"] == GQL_COMPLETE
    assert response["id"] == "demo"

    await client.send_json_to({"type": GQL_CONNECTION_TERMINATE})

    # make sure the websocket is disconnected now
    data = await client.receive_output()
    assert data == {"type": "websocket.close", "code": 1000}


async def test_resolving_enums(ws):
    await ws.send_json_to({"type": GQL_CONNECTION_INIT})
    await ws.send_json_to(
        {
            "type": GQL_START,
            "id": "demo",
            "payload": {
                "query": "subscription { flavors }",
            },
        }
    )

    response = await ws.receive_json_from()
    assert response["type"] == GQL_CONNECTION_ACK

    response = await ws.receive_json_from()
    assert response["type"] == GQL_DATA
    assert response["id"] == "demo"
    assert response["payload"]["data"] == {"flavors": "VANILLA"}

    response = await ws.receive_json_from()
    assert response["type"] == GQL_DATA
    assert response["id"] == "demo"
    assert response["payload"]["data"] == {"flavors": "STRAWBERRY"}

    response = await ws.receive_json_from()
    assert response["type"] == GQL_DATA
    assert response["id"] == "demo"
    assert response["payload"]["data"] == {"flavors": "CHOCOLATE"}

    await ws.send_json_to({"type": GQL_STOP, "id": "demo"})
    response = await ws.receive_json_from()
    assert response["type"] == GQL_COMPLETE
    assert response["id"] == "demo"

    await ws.send_json_to({"type": GQL_CONNECTION_TERMINATE})

    # make sure the websocket is disconnected now
    data = await ws.receive_output()
    assert data == {"type": "websocket.close", "code": 1000}


async def test_task_cancellation_separation():
    ws1 = WebsocketCommunicator(
        DebuggableGraphQLWSConsumer.as_asgi(
            schema=schema, subscription_protocols=(GRAPHQL_WS_PROTOCOL,)
        ),
        "/graphql",
        subprotocols=[
            GRAPHQL_WS_PROTOCOL,
        ],
    )
    res = await ws1.connect()
    assert res == (True, GRAPHQL_WS_PROTOCOL)
    ws2 = WebsocketCommunicator(
        DebuggableGraphQLWSConsumer.as_asgi(
            schema=schema, subscription_protocols=(GRAPHQL_WS_PROTOCOL,)
        ),
        "/graphql",
        subprotocols=[
            GRAPHQL_WS_PROTOCOL,
        ],
    )
    res = await ws2.connect()
    assert res == (True, GRAPHQL_WS_PROTOCOL)

    start_payload = {
        "type": GQL_START,
        "id": "demo",
        "payload": {"query": 'subscription { echo(message: "Hi", delay: 99) }'},
    }

    # 0 active result handler tasks

    await ws1.send_json_to({"type": GQL_CONNECTION_INIT})
    await ws1.send_json_to(start_payload)
    await ws1.receive_json_from()

    # 1 active result handler tasks

    await ws2.send_json_to({"type": GQL_CONNECTION_INIT})
    await ws2.send_json_to(start_payload)
    await ws2.receive_json_from()

    # 2 active result handler tasks

    await ws1.send_json_to({"type": GQL_STOP, "id": "demo"})
    await ws1.receive_json_from()  # complete

    # 1 active result handler tasks

    await ws2.send_json_to({"type": GQL_STOP, "id": "demo"})
    await ws2.receive_json_from()  # complete

    # 1 active result handler tasks

    await ws1.send_json_to(
        {
            "type": GQL_START,
            "id": "debug1",
            "payload": {
                "query": "subscription { debug { numActiveResultHandlers } }",
            },
        }
    )

    response = await ws1.receive_json_from()
    assert response["type"] == GQL_DATA
    assert response["id"] == "debug1"

    # The one active result handler is the one for this debug subscription
    assert response["payload"]["data"] == {"debug": {"numActiveResultHandlers": 1}}

    response = await ws1.receive_json_from()
    assert response["type"] == GQL_COMPLETE
    assert response["id"] == "debug1"
