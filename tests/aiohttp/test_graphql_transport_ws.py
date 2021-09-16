import asyncio
from datetime import timedelta

from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL
from strawberry.subscriptions.protocols.graphql_transport_ws.types import (
    CompleteMessage,
    ConnectionAckMessage,
    ConnectionInitMessage,
    NextMessage,
    PingMessage,
    PongMessage,
    SubscribeMessage,
    SubscribeMessagePayload,
)
from tests.aiohttp.app import create_app


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


async def test_connection_init_timeout(aiohttp_client):
    app = create_app(connection_init_wait_timeout=timedelta(seconds=0))
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        data = await ws.receive(timeout=2)
        assert ws.closed
        assert ws.close_code == 4408
        assert data.extra == "Connection initialisation timeout"


async def test_connection_init_timeout_cancellation(aiohttp_client):
    app = create_app(connection_init_wait_timeout=timedelta(milliseconds=100))
    aiohttp_app_client = await aiohttp_client(app)

    async with aiohttp_app_client.ws_connect(
        "/graphql", protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL]
    ) as ws:
        await ws.send_json(ConnectionInitMessage().as_dict())
        response = await ws.receive_json()
        assert response == ConnectionAckMessage().as_dict()

        await asyncio.sleep(0.11)
        # TODO: check task is done

        await ws.send_json(PingMessage().as_dict())

        response = await ws.receive_json()
        assert response == PongMessage().as_dict()

        await ws.close()
        assert ws.closed


async def test_unauthorized_subscriptions(aiohttp_client):
    pass


async def test_duplicated_operation_ids(aiohttp_client):
    pass


async def test_subscription_cancellation(aiohttp_client):
    pass


async def test_subscription_errors(aiohttp_client):
    pass


async def test_subscription_exceptions(aiohttp_client):
    pass


async def test_subscription_field_errors():
    pass


async def test_subscription_syntax_error(aiohttp_client):
    pass


async def test_ws_messages_must_be_text(aiohttp_client):
    pass


async def test_parsing_an_invalid_message(aiohttp_client):
    pass


async def test_unknown_message_types(aiohttp_client):
    pass
