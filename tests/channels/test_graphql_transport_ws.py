import asyncio
import json
from datetime import timedelta

import pytest

from channels.testing import WebsocketCommunicator
from strawberry.channels import GraphQLWSConsumer
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
from tests.channels.schema import schema


pytestmark = [
    pytest.mark.asyncio,
]


class DebuggableGraphQLTransportWSConsumer(GraphQLWSConsumer):
    async def get_context(self, *args, **kwargs) -> object:
        context = await super().get_context(*args, **kwargs)
        context.tasks = self._handler.tasks
        context.connectionInitTimeoutTask = self._handler.connection_init_timeout_task
        return context


@pytest.fixture
async def ws():
    client = WebsocketCommunicator(
        DebuggableGraphQLTransportWSConsumer.as_asgi(
            schema=schema, subscription_protocols=(GRAPHQL_TRANSPORT_WS_PROTOCOL,)
        ),
        "/graphql",
        subprotocols=[
            GRAPHQL_TRANSPORT_WS_PROTOCOL,
        ],
    )
    res = await client.connect()
    assert res == (True, GRAPHQL_TRANSPORT_WS_PROTOCOL)

    yield client

    await client.disconnect()


async def test_unknown_message_type(ws):
    await ws.send_json_to({"type": "NOT_A_MESSAGE_TYPE"})
    data = await ws.receive_output()

    assert data["type"] == "websocket.close"
    assert data["code"] == 4400


async def test_missing_message_type(ws):
    await ws.send_json_to({"notType": None})

    data = await ws.receive_output()
    assert data["type"] == "websocket.close"
    assert data["code"] == 4400


async def test_parsing_an_invalid_message(ws):
    await ws.send_json_to({"type": "subscribe", "notPayload": None})

    data = await ws.receive_output()
    assert data["type"] == "websocket.close"
    assert data["code"] == 4400


async def test_parsing_an_invalid_payload(ws):
    await ws.send_json_to({"type": "subscribe", "payload": {"unexpectedField": 42}})

    data = await ws.receive_output()
    assert data["type"] == "websocket.close"
    assert data["code"] == 4400


async def test_ws_messages_must_be_text(ws):
    await ws.send_to(bytes_data=json.dumps(ConnectionInitMessage().as_dict()).encode())

    data = await ws.receive_output()
    assert data["type"] == "websocket.close"
    assert data["code"] == 4400


async def test_connection_init_timeout():
    client = WebsocketCommunicator(
        GraphQLWSConsumer.as_asgi(
            schema=schema,
            connection_init_wait_timeout=timedelta(seconds=0),
            subscription_protocols=(GRAPHQL_TRANSPORT_WS_PROTOCOL,),
        ),
        "/graphql",
        subprotocols=[
            GRAPHQL_TRANSPORT_WS_PROTOCOL,
        ],
    )
    await asyncio.sleep(0.1)
    # Hope that the connection init timeout expired
    res = await client.connect()
    assert res == (True, GRAPHQL_TRANSPORT_WS_PROTOCOL)

    data = await client.receive_output()
    assert data["type"] == "websocket.close"
    assert data["code"] == 4408


async def test_connection_init_timeout_cancellation():
    client = WebsocketCommunicator(
        DebuggableGraphQLTransportWSConsumer.as_asgi(
            schema=schema,
            connection_init_wait_timeout=timedelta(milliseconds=500),
            subscription_protocols=(GRAPHQL_TRANSPORT_WS_PROTOCOL,),
        ),
        "/graphql",
        subprotocols=[
            GRAPHQL_TRANSPORT_WS_PROTOCOL,
        ],
    )
    await client.connect()
    await client.send_json_to(ConnectionInitMessage().as_dict())

    response = await client.receive_json_from()
    assert response == ConnectionAckMessage().as_dict()

    await asyncio.sleep(1)

    await client.send_json_to(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(
                query="subscription { debug { isConnectionInitTimeoutTaskDone } }"
            ),
        ).as_dict()
    )

    response = await client.receive_json_from()
    assert (
        response
        == NextMessage(
            id="sub1",
            payload={"data": {"debug": {"isConnectionInitTimeoutTaskDone": True}}},
        ).as_dict()
    )

    await client.disconnect()


async def test_too_many_initialisation_requests(ws):
    await ws.send_json_to(ConnectionInitMessage().as_dict())

    response = await ws.receive_json_from()
    assert response == ConnectionAckMessage().as_dict()

    await ws.send_json_to(ConnectionInitMessage().as_dict())

    data = await ws.receive_output()
    assert data["type"] == "websocket.close"
    assert data["code"] == 4429


async def test_ping_pong(ws):
    await ws.send_json_to(ConnectionInitMessage().as_dict())

    response = await ws.receive_json_from()
    assert response == ConnectionAckMessage().as_dict()

    await ws.send_json_to(PingMessage().as_dict())

    response = await ws.receive_json_from()
    assert response == PongMessage().as_dict()

    await ws.disconnect()


async def test_server_sent_ping(ws):
    await ws.send_json_to(ConnectionInitMessage().as_dict())

    response = await ws.receive_json_from()
    assert response == ConnectionAckMessage().as_dict()

    await ws.send_json_to(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(query="subscription { requestPing }"),
        ).as_dict()
    )

    response = await ws.receive_json_from()
    assert response == PingMessage().as_dict()

    await ws.send_json_to(PongMessage().as_dict())

    response = await ws.receive_json_from()
    assert (
        response
        == NextMessage(id="sub1", payload={"data": {"requestPing": True}}).as_dict()
    )

    response = await ws.receive_json_from()
    assert response == CompleteMessage(id="sub1").as_dict()

    await ws.disconnect()


async def test_unauthorized_subscriptions(ws):
    await ws.send_json_to(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(
                query='subscription { echo(message: "Hi") }'
            ),
        ).as_dict()
    )

    data = await ws.receive_output()
    assert data["type"] == "websocket.close"
    assert data["code"] == 4401


async def test_duplicated_operation_ids(ws):
    await ws.send_json_to(ConnectionInitMessage().as_dict())

    response = await ws.receive_json_from()
    assert response == ConnectionAckMessage().as_dict()

    await ws.send_json_to(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(
                query='subscription { echo(message: "Hi", delay: 5) }'
            ),
        ).as_dict()
    )

    await ws.send_json_to(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(
                query='subscription { echo(message: "Hi", delay: 5) }'
            ),
        ).as_dict()
    )

    data = await ws.receive_output()
    assert data["type"] == "websocket.close"
    assert data["code"] == 4409


async def test_simple_subscription(ws):
    await ws.send_json_to(ConnectionInitMessage().as_dict())

    response = await ws.receive_json_from()
    assert response == ConnectionAckMessage().as_dict()

    await ws.send_json_to(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(
                query='subscription { echo(message: "Hi") }'
            ),
        ).as_dict()
    )

    response = await ws.receive_json_from()
    assert (
        response == NextMessage(id="sub1", payload={"data": {"echo": "Hi"}}).as_dict()
    )

    await ws.send_json_to(CompleteMessage(id="sub1").as_dict())

    await ws.disconnect()


async def test_subscription_syntax_error(ws):
    await ws.send_json_to(ConnectionInitMessage().as_dict())

    response = await ws.receive_json_from()
    assert response == ConnectionAckMessage().as_dict()

    await ws.send_json_to(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(query="subscription { INVALID_SYNTAX "),
        ).as_dict()
    )

    response = await ws.receive_json_from()
    assert response["type"] == ErrorMessage.type
    assert response["id"] == "sub1"
    assert len(response["payload"]) == 1
    assert response["payload"][0]["path"] is None
    assert response["payload"][0]["locations"] == [{"line": 1, "column": 31}]
    assert (
        response["payload"][0]["message"] == "Syntax Error: Expected Name, found <EOF>."
    )

    await ws.disconnect()


async def test_subscription_field_errors(ws):
    await ws.send_json_to(ConnectionInitMessage().as_dict())

    response = await ws.receive_json_from()
    assert response == ConnectionAckMessage().as_dict()

    await ws.send_json_to(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(
                query="subscription { notASubscriptionField }",
            ),
        ).as_dict()
    )

    response = await ws.receive_json_from()
    assert response["type"] == ErrorMessage.type
    assert response["id"] == "sub1"
    assert len(response["payload"]) == 1
    assert response["payload"][0]["path"] is None
    assert response["payload"][0]["locations"] == [{"line": 1, "column": 16}]
    assert (
        response["payload"][0]["message"]
        == "The subscription field 'notASubscriptionField' is not defined."
    )

    await ws.disconnect()


async def test_subscription_cancellation(ws):
    await ws.send_json_to(ConnectionInitMessage().as_dict())

    response = await ws.receive_json_from()
    assert response == ConnectionAckMessage().as_dict()

    await ws.send_json_to(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(
                query='subscription { echo(message: "Hi", delay: 99) }'
            ),
        ).as_dict()
    )

    await ws.send_json_to(
        SubscribeMessage(
            id="sub2",
            payload=SubscribeMessagePayload(
                query="subscription { debug { numActiveResultHandlers } }",
            ),
        ).as_dict()
    )

    response = await ws.receive_json_from()
    assert (
        response
        == NextMessage(
            id="sub2", payload={"data": {"debug": {"numActiveResultHandlers": 2}}}
        ).as_dict()
    )

    response = await ws.receive_json_from()
    assert response == CompleteMessage(id="sub2").as_dict()

    await ws.send_json_to(CompleteMessage(id="sub1").as_dict())

    await ws.send_json_to(
        SubscribeMessage(
            id="sub3",
            payload=SubscribeMessagePayload(
                query="subscription { debug { numActiveResultHandlers } }",
            ),
        ).as_dict()
    )

    response = await ws.receive_json_from()
    assert (
        response
        == NextMessage(
            id="sub3", payload={"data": {"debug": {"numActiveResultHandlers": 1}}}
        ).as_dict()
    )

    response = await ws.receive_json_from()
    assert response == CompleteMessage(id="sub3").as_dict()

    await ws.disconnect()


async def test_subscription_errors(ws):
    await ws.send_json_to(ConnectionInitMessage().as_dict())

    response = await ws.receive_json_from()
    assert response == ConnectionAckMessage().as_dict()

    await ws.send_json_to(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(
                query='subscription { error(message: "TEST ERR") }',
            ),
        ).as_dict()
    )

    response = await ws.receive_json_from()
    assert response["type"] == ErrorMessage.type
    assert response["id"] == "sub1"
    assert len(response["payload"]) == 1
    assert response["payload"][0]["path"] == ["error"]
    assert response["payload"][0]["message"] == "TEST ERR"

    await ws.disconnect()


async def test_subscription_exceptions(ws):
    await ws.send_json_to(ConnectionInitMessage().as_dict())

    response = await ws.receive_json_from()
    assert response == ConnectionAckMessage().as_dict()

    await ws.send_json_to(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(
                query='subscription { exception(message: "TEST EXC") }',
            ),
        ).as_dict()
    )

    response = await ws.receive_json_from()
    assert response["type"] == ErrorMessage.type
    assert response["id"] == "sub1"
    assert len(response["payload"]) == 1
    assert response["payload"][0]["path"] is None
    assert response["payload"][0]["locations"] is None
    assert response["payload"][0]["message"] == "TEST EXC"

    await ws.disconnect()
