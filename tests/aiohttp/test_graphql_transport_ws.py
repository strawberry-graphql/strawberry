from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL
from strawberry.subscriptions.protocols.graphql_transport_ws.types import (
    CompleteMessage,
    ConnectionAckMessage,
    ConnectionInitMessage,
    NextMessage,
    SubscribeMessage,
    SubscribeMessagePayload,
)
from tests.aiohttp.app import create_app


async def test_simple_subscription(aiohttp_client):
    app = create_app(keep_alive=False)
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
