import asyncio
import json
from datetime import timedelta

import pytest

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


async def test_unknown_message_type(aiohttp_client):
    app = create_app()
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.send_json({"type": "NOT_A_MESSAGE_TYPE"})

        data = await ws.receive(timeout=2)
        assert ws.closed
        assert ws.close_code == 4400
        assert data.extra == "Unknown message type: NOT_A_MESSAGE_TYPE"


async def test_missing_message_type(aiohttp_client):
    app = create_app()
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.send_json({"notType": None})

        data = await ws.receive(timeout=2)
        assert ws.closed
        assert ws.close_code == 4400
        assert data.extra == "Failed to parse message"


async def test_parsing_an_invalid_message(aiohttp_client):
    app = create_app()
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.send_json({"type": "subscribe", "notPayload": None})

        data = await ws.receive(timeout=2)
        assert ws.closed
        assert ws.close_code == 4400
        assert data.extra == "Failed to parse message"


async def test_parsing_an_invalid_payload(aiohttp_client):
    app = create_app()
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.send_json({"type": "subscribe", "payload": {"unexpectedField": 42}})

        data = await ws.receive(timeout=2)
        assert ws.closed
        assert ws.close_code == 4400
        assert data.extra == "Failed to parse message"


async def test_ws_messages_must_be_text(aiohttp_client):
    app = create_app()
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.send_bytes(json.dumps(ConnectionInitMessage().as_dict()).encode())

        data = await ws.receive(timeout=2)
        assert ws.closed
        assert ws.close_code == 4400
        assert data.extra == "WebSocket message type must be text"


@pytest.mark.xfail(
    reason="Closing a AIOHTTP WebSocket from a task currently doesnt work as expected",
)
async def test_connection_init_timeout(aiohttp_client):
    app = create_app(connection_init_wait_timeout=timedelta(seconds=0))
    aiohttp_app_client = await aiohttp_client(app)

    # Make sure the connection init timeout expired
    await asyncio.sleep(0.1)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        data = await ws.receive(timeout=2)
        assert ws.closed
        assert ws.close_code == 4408
        assert data.extra == "Connection initialisation timeout"


async def test_connection_init_timeout_cancellation(aiohttp_client):
    app = create_app(connection_init_wait_timeout=timedelta(milliseconds=50))
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
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


async def test_too_many_initialisation_requests(aiohttp_client):
    app = create_app()
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.send_json(ConnectionInitMessage().as_dict())

        response = await ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

        await ws.send_json(ConnectionInitMessage().as_dict())

        data = await ws.receive(timeout=2)
        assert ws.closed
        assert ws.close_code == 4429
        assert data.extra == "Too many initialisation requests"


async def test_ping_pong(aiohttp_client):
    app = create_app()
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.send_json(ConnectionInitMessage().as_dict())

        response = await ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

        await ws.send_json(PingMessage().as_dict())

        response = await ws.receive_json()
        assert response == PongMessage().as_dict()

        await ws.close()
        assert ws.closed


async def test_server_sent_ping(aiohttp_client):
    app = create_app()
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.send_json(ConnectionInitMessage().as_dict())

        response = await ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

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

        await ws.close()
        assert ws.closed


async def test_unauthorized_subscriptions(aiohttp_client):
    app = create_app()
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
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
        assert data.extra == "Unauthorized"


async def test_duplicated_operation_ids(aiohttp_client):
    app = create_app()
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.send_json(ConnectionInitMessage().as_dict())

        response = await ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

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
        assert data.extra == "Subscriber for sub1 already exists"


async def test_simple_subscription(aiohttp_client):
    app = create_app()
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.send_json(ConnectionInitMessage().as_dict())

        response = await ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

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

        await ws.close()
        assert ws.closed


async def test_subscription_syntax_error(aiohttp_client):
    app = create_app()
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.send_json(ConnectionInitMessage().as_dict())

        response = await ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

        await ws.send_json(
            SubscribeMessage(
                id="sub1",
                payload=SubscribeMessagePayload(query="subscription { INVALID_SYNTAX "),
            ).as_dict()
        )

        data = await ws.receive(timeout=2)
        assert ws.closed
        assert ws.close_code == 4400
        assert data.extra == "Syntax Error: Expected Name, found <EOF>."


async def test_subscription_field_errors(aiohttp_client):
    app = create_app()
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.send_json(ConnectionInitMessage().as_dict())

        response = await ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

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

        await ws.close()
        assert ws.closed


async def test_subscription_cancellation(aiohttp_client):
    app = create_app()
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.send_json(ConnectionInitMessage().as_dict())

        response = await ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

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

        await ws.close()
        assert ws.closed


async def test_subscription_errors(aiohttp_client):
    app = create_app()
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.send_json(ConnectionInitMessage().as_dict())

        response = await ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

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

        await ws.close()
        assert ws.closed


async def test_subscription_exceptions(aiohttp_client):
    app = create_app()
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.send_json(ConnectionInitMessage().as_dict())

        response = await ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

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

        await ws.close()
        assert ws.closed


async def test_single_result_query_operation(aiohttp_client):
    app = create_app()
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.send_json(ConnectionInitMessage().as_dict())

        response = await ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

        await ws.send_json(
            SubscribeMessage(
                id="sub1",
                payload=SubscribeMessagePayload(query="query { hello }"),
            ).as_dict()
        )

        response = await ws.receive_json()
        assert (
            response
            == NextMessage(
                id="sub1", payload={"data": {"hello": "Hello world"}}
            ).as_dict()
        )

        response = await ws.receive_json()
        assert response == CompleteMessage(id="sub1").as_dict()

        await ws.close()
        assert ws.closed


async def test_single_result_mutation_operation(aiohttp_client):
    app = create_app()
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.send_json(ConnectionInitMessage().as_dict())

        response = await ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

        await ws.send_json(
            SubscribeMessage(
                id="sub1",
                payload=SubscribeMessagePayload(query="mutation { hello }"),
            ).as_dict()
        )

        response = await ws.receive_json()
        assert (
            response
            == NextMessage(
                id="sub1", payload={"data": {"hello": "strawberry"}}
            ).as_dict()
        )

        response = await ws.receive_json()
        assert response == CompleteMessage(id="sub1").as_dict()

        await ws.close()
        assert ws.closed


async def test_single_result_operation_selection(aiohttp_client):
    app = create_app()
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.send_json(ConnectionInitMessage().as_dict())

        response = await ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

        query = """
            query Query1 {
                hello
            }
            query Query2 {
                hello(name: "Strawberry")
            }
        """

        await ws.send_json(
            SubscribeMessage(
                id="sub1",
                payload=SubscribeMessagePayload(query=query, operationName="Query2"),
            ).as_dict()
        )

        response = await ws.receive_json()
        assert (
            response
            == NextMessage(
                id="sub1", payload={"data": {"hello": "Hello Strawberry"}}
            ).as_dict()
        )

        response = await ws.receive_json()
        assert response == CompleteMessage(id="sub1").as_dict()

        await ws.close()
        assert ws.closed


async def test_single_result_invalid_operation_selection(aiohttp_client):
    app = create_app()
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.send_json(ConnectionInitMessage().as_dict())

        response = await ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

        query = """
            query Query1 {
                hello
            }
        """

        await ws.send_json(
            SubscribeMessage(
                id="sub1",
                payload=SubscribeMessagePayload(query=query, operationName="Query2"),
            ).as_dict()
        )

        data = await ws.receive(timeout=2)
        assert ws.closed
        assert ws.close_code == 4400
        assert data.extra == "Can't get GraphQL operation type"


async def test_single_result_operation_error(aiohttp_client):
    app = create_app()
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.send_json(ConnectionInitMessage().as_dict())

        response = await ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

        await ws.send_json(
            SubscribeMessage(
                id="sub1",
                payload=SubscribeMessagePayload(
                    query="query { alwaysFail }",
                ),
            ).as_dict()
        )

        response = await ws.receive_json()
        assert response["type"] == ErrorMessage.type
        assert response["id"] == "sub1"
        assert len(response["payload"]) == 1
        assert response["payload"][0]["message"] == "You are not authorized"

        await ws.close()
        assert ws.closed


async def test_subscription_complete_race(aiohttp_client):
    """Issue #1731
    Test that sending a complete message after server
    has already completed doesn't cause problems.
    """
    app = create_app()
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.send_json(ConnectionInitMessage().as_dict())

        response = await ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

        await ws.send_json(
            SubscribeMessage(
                id="sub1",
                payload=SubscribeMessagePayload(
                    query="subscription { debug { numActiveResultHandlers } }",
                ),
            ).as_dict()
        )

        response = await ws.receive_json()
        assert (
            response
            == NextMessage(
                id="sub1", payload={"data": {"debug": {"numActiveResultHandlers": 1}}}
            ).as_dict()
        )

        response = await ws.receive_json()
        assert response == CompleteMessage(id="sub1").as_dict()

        # Imagine that we didn'r receive the CompleteMessage from server and
        # issue one of our own.  It should be ignored by the server.
        # Verify this by making a new subscription
        await ws.send_json(CompleteMessage(id="sub1").as_dict())

        # make a new subscription
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
                id="sub2", payload={"data": {"debug": {"numActiveResultHandlers": 1}}}
            ).as_dict()
        )

        await ws.close()
        assert ws.closed


async def test_single_result_complete(aiohttp_client):
    """Issue #1731
    Make sure we can `complete` a single result operation
    """
    app = create_app()
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.send_json(ConnectionInitMessage().as_dict())

        response = await ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

        await ws.send_json(
            SubscribeMessage(
                id="sub1",
                payload=SubscribeMessagePayload(query="query { hello }"),
            ).as_dict()
        )
        # complete it before getting a result
        await ws.send_json(CompleteMessage(id="sub1").as_dict())

        # send another request, to make sure we get a response and
        # the socket doesn't stay silent
        await ws.send_json(
            SubscribeMessage(
                id="sub2",
                payload=SubscribeMessagePayload(query="query { hello }"),
            ).as_dict()
        )

        # discard stale `next` or `complete` messages from sub1
        # (in case our `complete` was too late)
        response = await ws.receive_json()
        next1 = NextMessage(
            id="sub1", payload={"data": {"hello": "Hello world"}}
        ).as_dict()
        comp1 = CompleteMessage(id="sub1").as_dict()
        if response == next1:
            response = await ws.receive_json()
        if response == comp1:
            response = await ws.receive_json()

        assert (
            response
            == NextMessage(
                id="sub2", payload={"data": {"hello": "Hello world"}}
            ).as_dict()
        )

        # discard stale sub1 messages that may be arriving here
        response = await ws.receive_json()
        if response == next1:
            response = await ws.receive_json()
        if response == comp1:
            response = await ws.receive_json()
        assert response == CompleteMessage(id="sub2").as_dict()
