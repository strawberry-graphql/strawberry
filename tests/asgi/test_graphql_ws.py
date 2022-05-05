import pytest

from starlette.websockets import WebSocketDisconnect

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


def test_simple_subscription(test_client):
    with test_client.websocket_connect("/", [GRAPHQL_WS_PROTOCOL]) as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GQL_START,
                "id": "demo",
                "payload": {
                    "query": 'subscription { echo(message: "Hi") }',
                },
            }
        )

        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK

        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "demo"
        assert response["payload"]["data"] == {"echo": "Hi"}

        ws.send_json({"type": GQL_STOP, "id": "demo"})
        response = ws.receive_json()
        assert response["type"] == GQL_COMPLETE
        assert response["id"] == "demo"

        ws.send_json({"type": GQL_CONNECTION_TERMINATE})

        # make sure the websocket is disconnected now
        with pytest.raises(WebSocketDisconnect):
            ws.receive_json()


def test_operation_selection(test_client):
    with test_client.websocket_connect("/", [GRAPHQL_WS_PROTOCOL]) as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        ws.send_json(
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

        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK

        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "demo"
        assert response["payload"]["data"] == {"echo": "Hi2"}

        ws.send_json({"type": GQL_STOP, "id": "demo"})
        response = ws.receive_json()
        assert response["type"] == GQL_COMPLETE
        assert response["id"] == "demo"

        ws.send_json({"type": GQL_CONNECTION_TERMINATE})

        # make sure the websocket is disconnected now
        with pytest.raises(WebSocketDisconnect):
            ws.receive_json()


def test_sends_keep_alive(test_client_keep_alive):
    with test_client_keep_alive.websocket_connect("/", [GRAPHQL_WS_PROTOCOL]) as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GQL_START,
                "id": "demo",
                "payload": {
                    "query": 'subscription { echo(message: "Hi", delay: 0.15) }'
                },
            }
        )

        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK

        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_KEEP_ALIVE

        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_KEEP_ALIVE

        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "demo"
        assert response["payload"]["data"] == {"echo": "Hi"}

        response = ws.receive_json()
        assert response["type"] == GQL_COMPLETE
        assert response["id"] == "demo"

        ws.send_json({"type": GQL_CONNECTION_TERMINATE})


def test_subscription_cancellation(test_client):
    with test_client.websocket_connect("/", [GRAPHQL_WS_PROTOCOL]) as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK

        ws.send_json(
            {
                "type": GQL_START,
                "id": "demo",
                "payload": {"query": 'subscription { echo(message: "Hi", delay: 99) }'},
            }
        )

        ws.send_json(
            {
                "type": GQL_START,
                "id": "debug1",
                "payload": {
                    "query": "subscription { debug { numActiveResultHandlers } }",
                },
            }
        )

        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "debug1"
        assert response["payload"]["data"] == {"debug": {"numActiveResultHandlers": 2}}

        response = ws.receive_json()
        assert response["type"] == GQL_COMPLETE
        assert response["id"] == "debug1"

        ws.send_json({"type": GQL_STOP, "id": "demo"})
        response = ws.receive_json()
        assert response["type"] == GQL_COMPLETE
        assert response["id"] == "demo"

        ws.send_json(
            {
                "type": GQL_START,
                "id": "debug2",
                "payload": {
                    "query": "subscription { debug { numActiveResultHandlers} }",
                },
            }
        )

        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "debug2"
        assert response["payload"]["data"] == {"debug": {"numActiveResultHandlers": 1}}

        response = ws.receive_json()
        assert response["type"] == GQL_COMPLETE
        assert response["id"] == "debug2"

        ws.send_json({"type": GQL_CONNECTION_TERMINATE})

        # make sure the websocket is disconnected now
        with pytest.raises(WebSocketDisconnect):
            ws.receive_json()


def test_subscription_errors(test_client):
    with test_client.websocket_connect("/", [GRAPHQL_WS_PROTOCOL]) as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GQL_START,
                "id": "demo",
                "payload": {"query": 'subscription { error(message: "TEST ERR") }'},
            }
        )

        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK

        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "demo"
        assert response["payload"]["data"] is None
        assert response["payload"]["errors"][0]["path"] == ["error"]
        assert response["payload"]["errors"][0]["message"] == "TEST ERR"

        response = ws.receive_json()
        assert response["type"] == GQL_COMPLETE
        assert response["id"] == "demo"

        ws.send_json({"type": GQL_CONNECTION_TERMINATE})

        # make sure the websocket is disconnected now
        with pytest.raises(WebSocketDisconnect):
            ws.receive_json()


def test_subscription_exceptions(test_client):
    with test_client.websocket_connect("/", [GRAPHQL_WS_PROTOCOL]) as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GQL_START,
                "id": "demo",
                "payload": {"query": 'subscription { exception(message: "TEST EXC") }'},
            }
        )

        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK

        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "demo"
        assert response["payload"]["data"] is None
        assert response["payload"]["errors"] == [{"message": "TEST EXC"}]

        ws.send_json({"type": GQL_STOP, "id": "demo"})
        response = ws.receive_json()
        assert response["type"] == GQL_COMPLETE
        assert response["id"] == "demo"

        ws.send_json({"type": GQL_CONNECTION_TERMINATE})

        # make sure the websocket is disconnected now
        with pytest.raises(WebSocketDisconnect):
            ws.receive_json()


def test_subscription_field_error(test_client):
    with test_client.websocket_connect("/", [GRAPHQL_WS_PROTOCOL]) as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GQL_START,
                "id": "invalid-field",
                "payload": {"query": "subscription { notASubscriptionField }"},
            }
        )

        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK

        response = ws.receive_json()
        assert response["type"] == GQL_ERROR
        assert response["id"] == "invalid-field"
        assert response["payload"] == {
            "locations": [{"line": 1, "column": 16}],
            "message": (
                "The subscription field 'notASubscriptionField' is not defined."
            ),
        }

        ws.send_json({"type": GQL_CONNECTION_TERMINATE})

        # make sure the websocket is disconnected now
        with pytest.raises(WebSocketDisconnect):
            ws.receive_json()


def test_subscription_syntax_error(test_client):
    with test_client.websocket_connect("/", [GRAPHQL_WS_PROTOCOL]) as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GQL_START,
                "id": "syntax-error",
                "payload": {"query": "subscription { example "},
            }
        )

        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK

        response = ws.receive_json()
        assert response["type"] == GQL_ERROR
        assert response["id"] == "syntax-error"
        assert response["payload"] == {
            "locations": [{"line": 1, "column": 24}],
            "message": "Syntax Error: Expected Name, found <EOF>.",
        }

        ws.send_json({"type": GQL_CONNECTION_TERMINATE})

        # make sure the websocket is disconnected now
        with pytest.raises(WebSocketDisconnect):
            ws.receive_json()


def test_non_text_ws_messages_are_ignored(test_client):
    with test_client.websocket_connect("/", [GRAPHQL_WS_PROTOCOL]) as ws:
        ws.send_bytes(b"")
        ws.send_json({"type": GQL_CONNECTION_INIT})

        ws.send_bytes(b"")
        ws.send_json(
            {
                "type": GQL_START,
                "id": "demo",
                "payload": {
                    "query": 'subscription { echo(message: "Hi") }',
                },
            }
        )

        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK

        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "demo"
        assert response["payload"]["data"] == {"echo": "Hi"}

        ws.send_bytes(b"")
        ws.send_json({"type": GQL_STOP, "id": "demo"})
        response = ws.receive_json()
        assert response["type"] == GQL_COMPLETE
        assert response["id"] == "demo"

        ws.send_bytes(b"")
        ws.send_json({"type": GQL_CONNECTION_TERMINATE})

        # make sure the websocket is disconnected now
        with pytest.raises(WebSocketDisconnect):
            ws.receive_json()


def test_unknown_protocol_messages_are_ignored(test_client):
    with test_client.websocket_connect("/", [GRAPHQL_WS_PROTOCOL]) as ws:
        ws.send_json({"type": "NotAProtocolMessage"})
        ws.send_json({"type": GQL_CONNECTION_INIT})

        ws.send_json({"type": "NotAProtocolMessage"})
        ws.send_json(
            {
                "type": GQL_START,
                "id": "demo",
                "payload": {
                    "query": 'subscription { echo(message: "Hi") }',
                },
            }
        )

        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK

        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "demo"
        assert response["payload"]["data"] == {"echo": "Hi"}

        ws.send_json({"type": "NotAProtocolMessage"})
        ws.send_json({"type": GQL_STOP, "id": "demo"})
        response = ws.receive_json()
        assert response["type"] == GQL_COMPLETE
        assert response["id"] == "demo"

        ws.send_json({"type": "NotAProtocolMessage"})
        ws.send_json({"type": GQL_CONNECTION_TERMINATE})

        # make sure the websocket is disconnected now
        with pytest.raises(WebSocketDisconnect):
            ws.receive_json()


def test_custom_context(test_client):
    with test_client.websocket_connect("/", [GRAPHQL_WS_PROTOCOL]) as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GQL_START,
                "id": "demo",
                "payload": {
                    "query": "subscription { context }",
                },
            }
        )

        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK

        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "demo"
        assert response["payload"]["data"] == {"context": "Hi"}

        ws.send_json({"type": GQL_STOP, "id": "demo"})
        response = ws.receive_json()
        assert response["type"] == GQL_COMPLETE
        assert response["id"] == "demo"

        ws.send_json({"type": GQL_CONNECTION_TERMINATE})

        # make sure the websocket is disconnected now
        with pytest.raises(WebSocketDisconnect):
            ws.receive_json()


def test_resolving_enums(test_client):
    with test_client.websocket_connect("/", [GRAPHQL_WS_PROTOCOL]) as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GQL_START,
                "id": "demo",
                "payload": {
                    "query": "subscription { flavors }",
                },
            }
        )

        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK

        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "demo"
        assert response["payload"]["data"] == {"flavors": "VANILLA"}

        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "demo"
        assert response["payload"]["data"] == {"flavors": "STRAWBERRY"}

        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "demo"
        assert response["payload"]["data"] == {"flavors": "CHOCOLATE"}

        ws.send_json({"type": GQL_STOP, "id": "demo"})
        response = ws.receive_json()
        assert response["type"] == GQL_COMPLETE
        assert response["id"] == "demo"

        ws.send_json({"type": GQL_CONNECTION_TERMINATE})

        # make sure the websocket is disconnected now
        with pytest.raises(WebSocketDisconnect):
            ws.receive_json()


def test_task_cancellation_separation(test_client):
    connection1 = test_client.websocket_connect("/", [GRAPHQL_WS_PROTOCOL])
    connection2 = test_client.websocket_connect("/", [GRAPHQL_WS_PROTOCOL])

    with connection1 as ws1, connection2 as ws2:
        start_payload = {
            "type": GQL_START,
            "id": "demo",
            "payload": {"query": 'subscription { echo(message: "Hi", delay: 99) }'},
        }

        # 0 active result handler tasks

        ws1.send_json({"type": GQL_CONNECTION_INIT})
        ws1.send_json(start_payload)
        ws1.receive_json()

        # 1 active result handler tasks

        ws2.send_json({"type": GQL_CONNECTION_INIT})
        ws2.send_json(start_payload)
        ws2.receive_json()

        # 2 active result handler tasks

        ws1.send_json({"type": GQL_STOP, "id": "demo"})
        ws1.receive_json()  # complete

        # 1 active result handler tasks

        ws2.send_json({"type": GQL_STOP, "id": "demo"})
        ws2.receive_json()  # complete

        # 1 active result handler tasks

        ws1.send_json(
            {
                "type": GQL_START,
                "id": "debug1",
                "payload": {
                    "query": "subscription { debug { numActiveResultHandlers } }",
                },
            }
        )

        response = ws1.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "debug1"

        # The one active result handler is the one for this debug subscription
        assert response["payload"]["data"] == {"debug": {"numActiveResultHandlers": 1}}

        response = ws1.receive_json()
        assert response["type"] == GQL_COMPLETE
        assert response["id"] == "debug1"
