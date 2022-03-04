import asyncio
import json
from datetime import timedelta

from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

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
from tests.fastapi.app import create_app


def test_unknown_message_type(test_client):
    with test_client.websocket_connect(
        "/graphql", [GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        ws.send_json({"type": "NOT_A_MESSAGE_TYPE"})

        data = ws.receive()
        assert data["type"] == "websocket.close"
        assert data["code"] == 4400


def test_missing_message_type(test_client):
    with test_client.websocket_connect(
        "/graphql", [GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        ws.send_json({"notType": None})

        data = ws.receive()
        assert data["type"] == "websocket.close"
        assert data["code"] == 4400


def test_parsing_an_invalid_message(test_client):
    with test_client.websocket_connect(
        "/graphql", [GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        ws.send_json({"type": "subscribe", "notPayload": None})

        data = ws.receive()
        assert data["type"] == "websocket.close"
        assert data["code"] == 4400


def test_parsing_an_invalid_payload(test_client):
    with test_client.websocket_connect(
        "/graphql", [GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        ws.send_json({"type": "subscribe", "payload": {"unexpectedField": 42}})

        data = ws.receive()
        assert data["type"] == "websocket.close"
        assert data["code"] == 4400


def test_ws_messages_must_be_text(test_client):
    with test_client.websocket_connect(
        "/graphql", [GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        ws.send_bytes(json.dumps(ConnectionInitMessage().as_dict()).encode())

        data = ws.receive()
        assert data["type"] == "websocket.close"
        assert data["code"] == 4400


async def test_connection_init_timeout():
    app = create_app(connection_init_wait_timeout=timedelta(seconds=0))
    test_client = TestClient(app)

    # Hope that the connection init timeout expired
    await asyncio.sleep(0.1)

    try:
        with test_client.websocket_connect(
            "/graphql", [GRAPHQL_TRANSPORT_WS_PROTOCOL]
        ) as ws:
            data = ws.receive()
            assert data["type"] == "websocket.close"
            assert data["code"] == 4408
    except WebSocketDisconnect as exc:
        assert exc.code == 4408


async def test_connection_init_timeout_cancellation(test_client):
    app = create_app(connection_init_wait_timeout=timedelta(milliseconds=500))
    test_client = TestClient(app)

    with test_client.websocket_connect(
        "/graphql", [GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        ws.send_json(ConnectionInitMessage().as_dict())

        response = ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

        await asyncio.sleep(1)

        ws.send_json(
            SubscribeMessage(
                id="sub1",
                payload=SubscribeMessagePayload(
                    query="subscription { debug { isConnectionInitTimeoutTaskDone } }"
                ),
            ).as_dict()
        )

        response = ws.receive_json()
        assert (
            response
            == NextMessage(
                id="sub1",
                payload={"data": {"debug": {"isConnectionInitTimeoutTaskDone": True}}},
            ).as_dict()
        )

        ws.close()


def test_too_many_initialisation_requests(test_client):
    with test_client.websocket_connect(
        "/graphql", [GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        ws.send_json(ConnectionInitMessage().as_dict())

        response = ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

        ws.send_json(ConnectionInitMessage().as_dict())

        data = ws.receive()
        assert data["type"] == "websocket.close"
        assert data["code"] == 4429


def test_ping_pong(test_client):
    with test_client.websocket_connect(
        "/graphql", [GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        ws.send_json(ConnectionInitMessage().as_dict())

        response = ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

        ws.send_json(PingMessage().as_dict())

        response = ws.receive_json()
        assert response == PongMessage().as_dict()

        ws.close()


def test_server_sent_ping(test_client):
    with test_client.websocket_connect(
        "/graphql", [GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        ws.send_json(ConnectionInitMessage().as_dict())

        response = ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

        ws.send_json(
            SubscribeMessage(
                id="sub1",
                payload=SubscribeMessagePayload(query="subscription { requestPing }"),
            ).as_dict()
        )

        response = ws.receive_json()
        assert response == PingMessage().as_dict()

        ws.send_json(PongMessage().as_dict())

        response = ws.receive_json()
        assert (
            response
            == NextMessage(id="sub1", payload={"data": {"requestPing": True}}).as_dict()
        )

        response = ws.receive_json()
        assert response == CompleteMessage(id="sub1").as_dict()

        ws.close()


def test_unauthorized_subscriptions(test_client):
    with test_client.websocket_connect(
        "/graphql", [GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        ws.send_json(
            SubscribeMessage(
                id="sub1",
                payload=SubscribeMessagePayload(
                    query='subscription { echo(message: "Hi") }'
                ),
            ).as_dict()
        )

        data = ws.receive()
        assert data["type"] == "websocket.close"
        assert data["code"] == 4401


def test_duplicated_operation_ids(test_client):
    with test_client.websocket_connect(
        "/graphql", [GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        ws.send_json(ConnectionInitMessage().as_dict())

        response = ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

        ws.send_json(
            SubscribeMessage(
                id="sub1",
                payload=SubscribeMessagePayload(
                    query='subscription { echo(message: "Hi", delay: 5) }'
                ),
            ).as_dict()
        )

        ws.send_json(
            SubscribeMessage(
                id="sub1",
                payload=SubscribeMessagePayload(
                    query='subscription { echo(message: "Hi", delay: 5) }'
                ),
            ).as_dict()
        )

        data = ws.receive()
        assert data["type"] == "websocket.close"
        assert data["code"] == 4409


def test_simple_subscription(test_client):
    with test_client.websocket_connect(
        "/graphql", [GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        ws.send_json(ConnectionInitMessage().as_dict())

        response = ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

        ws.send_json(
            SubscribeMessage(
                id="sub1",
                payload=SubscribeMessagePayload(
                    query='subscription { echo(message: "Hi") }'
                ),
            ).as_dict()
        )

        response = ws.receive_json()
        assert (
            response
            == NextMessage(id="sub1", payload={"data": {"echo": "Hi"}}).as_dict()
        )

        ws.send_json(CompleteMessage(id="sub1").as_dict())

        ws.close()


def test_subscription_syntax_error(test_client):
    with test_client.websocket_connect(
        "/graphql", [GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        ws.send_json(ConnectionInitMessage().as_dict())

        response = ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

        ws.send_json(
            SubscribeMessage(
                id="sub1",
                payload=SubscribeMessagePayload(query="subscription { INVALID_SYNTAX "),
            ).as_dict()
        )

        data = ws.receive()
        assert data["type"] == "websocket.close"
        assert data["code"] == 4400


def test_subscription_field_errors(test_client):
    with test_client.websocket_connect(
        "/graphql", [GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        ws.send_json(ConnectionInitMessage().as_dict())

        response = ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

        ws.send_json(
            SubscribeMessage(
                id="sub1",
                payload=SubscribeMessagePayload(
                    query="subscription { notASubscriptionField }",
                ),
            ).as_dict()
        )

        response = ws.receive_json()
        assert response["type"] == ErrorMessage.type
        assert response["id"] == "sub1"
        assert len(response["payload"]) == 1
        assert response["payload"][0].get("path") is None
        assert response["payload"][0]["locations"] == [{"line": 1, "column": 16}]
        assert (
            response["payload"][0]["message"]
            == "The subscription field 'notASubscriptionField' is not defined."
        )

        ws.close()


def test_subscription_cancellation(test_client):
    with test_client.websocket_connect(
        "/graphql", [GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        ws.send_json(ConnectionInitMessage().as_dict())

        response = ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

        ws.send_json(
            SubscribeMessage(
                id="sub1",
                payload=SubscribeMessagePayload(
                    query='subscription { echo(message: "Hi", delay: 99) }'
                ),
            ).as_dict()
        )

        ws.send_json(
            SubscribeMessage(
                id="sub2",
                payload=SubscribeMessagePayload(
                    query="subscription { debug { numActiveResultHandlers } }",
                ),
            ).as_dict()
        )

        response = ws.receive_json()
        assert (
            response
            == NextMessage(
                id="sub2", payload={"data": {"debug": {"numActiveResultHandlers": 2}}}
            ).as_dict()
        )

        response = ws.receive_json()
        assert response == CompleteMessage(id="sub2").as_dict()

        ws.send_json(CompleteMessage(id="sub1").as_dict())

        ws.send_json(
            SubscribeMessage(
                id="sub3",
                payload=SubscribeMessagePayload(
                    query="subscription { debug { numActiveResultHandlers } }",
                ),
            ).as_dict()
        )

        response = ws.receive_json()
        assert (
            response
            == NextMessage(
                id="sub3", payload={"data": {"debug": {"numActiveResultHandlers": 1}}}
            ).as_dict()
        )

        response = ws.receive_json()
        assert response == CompleteMessage(id="sub3").as_dict()

        ws.close()


def test_subscription_errors(test_client):
    with test_client.websocket_connect(
        "/graphql", [GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        ws.send_json(ConnectionInitMessage().as_dict())

        response = ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

        ws.send_json(
            SubscribeMessage(
                id="sub1",
                payload=SubscribeMessagePayload(
                    query='subscription { error(message: "TEST ERR") }',
                ),
            ).as_dict()
        )

        response = ws.receive_json()
        assert response["type"] == ErrorMessage.type
        assert response["id"] == "sub1"
        assert len(response["payload"]) == 1
        assert response["payload"][0]["path"] == ["error"]
        assert response["payload"][0]["message"] == "TEST ERR"

        ws.close()


def test_subscription_exceptions(test_client):
    with test_client.websocket_connect(
        "/graphql", [GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        ws.send_json(ConnectionInitMessage().as_dict())

        response = ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

        ws.send_json(
            SubscribeMessage(
                id="sub1",
                payload=SubscribeMessagePayload(
                    query='subscription { exception(message: "TEST EXC") }',
                ),
            ).as_dict()
        )

        response = ws.receive_json()
        assert response["type"] == ErrorMessage.type
        assert response["id"] == "sub1"
        assert len(response["payload"]) == 1
        assert response["payload"][0].get("path") is None
        assert response["payload"][0].get("locations") is None
        assert response["payload"][0]["message"] == "TEST EXC"

        ws.close()


def test_single_result_query_operation(test_client):
    with test_client.websocket_connect(
        "/graphql", [GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        ws.send_json(ConnectionInitMessage().as_dict())

        response = ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

        ws.send_json(
            SubscribeMessage(
                id="sub1",
                payload=SubscribeMessagePayload(query="query { hello }"),
            ).as_dict()
        )

        response = ws.receive_json()
        assert (
            response
            == NextMessage(
                id="sub1", payload={"data": {"hello": "Hello world"}}
            ).as_dict()
        )

        response = ws.receive_json()
        assert response == CompleteMessage(id="sub1").as_dict()


def test_single_result_mutation_operation(test_client):
    with test_client.websocket_connect(
        "/graphql", [GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        ws.send_json(ConnectionInitMessage().as_dict())

        response = ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

        ws.send_json(
            SubscribeMessage(
                id="sub1",
                payload=SubscribeMessagePayload(query="mutation { hello }"),
            ).as_dict()
        )

        response = ws.receive_json()
        assert (
            response
            == NextMessage(
                id="sub1", payload={"data": {"hello": "strawberry"}}
            ).as_dict()
        )

        response = ws.receive_json()
        assert response == CompleteMessage(id="sub1").as_dict()


def test_single_result_operation_selection(test_client):
    with test_client.websocket_connect(
        "/graphql", [GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        ws.send_json(ConnectionInitMessage().as_dict())

        response = ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

        query = """
            query Query1 {
                hello
            }
            query Query2 {
                hello(name: "Strawberry")
            }
        """

        ws.send_json(
            SubscribeMessage(
                id="sub1",
                payload=SubscribeMessagePayload(query=query, operationName="Query2"),
            ).as_dict()
        )

        response = ws.receive_json()
        assert (
            response
            == NextMessage(
                id="sub1", payload={"data": {"hello": "Hello Strawberry"}}
            ).as_dict()
        )

        response = ws.receive_json()
        assert response == CompleteMessage(id="sub1").as_dict()


def test_single_result_invalid_operation_selection(test_client):
    with test_client.websocket_connect(
        "/graphql", [GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        ws.send_json(ConnectionInitMessage().as_dict())

        response = ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

        query = """
            query Query1 {
                hello
            }
        """

        ws.send_json(
            SubscribeMessage(
                id="sub1",
                payload=SubscribeMessagePayload(query=query, operationName="Query2"),
            ).as_dict()
        )

        data = ws.receive()
        assert data["type"] == "websocket.close"
        assert data["code"] == 4400


def test_single_result_operation_error(test_client):
    with test_client.websocket_connect(
        "/graphql", [GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        ws.send_json(ConnectionInitMessage().as_dict())

        response = ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

        ws.send_json(
            SubscribeMessage(
                id="sub1",
                payload=SubscribeMessagePayload(
                    query="query { alwaysFail }",
                ),
            ).as_dict()
        )

        response = ws.receive_json()
        assert response["type"] == ErrorMessage.type
        assert response["id"] == "sub1"
        assert len(response["payload"]) == 1
        assert response["payload"][0]["message"] == "You are not authorized"
