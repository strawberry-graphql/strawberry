import pytest

from channels.testing.websocket import WebsocketCommunicator
from strawberry.channels.handlers.graphql_transport_ws_handler import (
    GraphQLTransportWSHandler,
)
from strawberry.channels.handlers.graphql_ws_handler import GraphQLWSHandler
from strawberry.channels.handlers.ws_handler import GraphQLWSConsumer
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL
from tests.channels.schema import schema


async def test_wrong_protocol():
    GraphQLWSConsumer.as_asgi(schema=schema),
    client = WebsocketCommunicator(
        GraphQLWSConsumer.as_asgi(schema=schema),
        "/graphql",
        subprotocols=[
            "non-existing",
        ],
    )
    res = await client.connect()
    assert res == (False, 4406)


@pytest.mark.parametrize(
    "protocol,handler",
    [
        (GRAPHQL_TRANSPORT_WS_PROTOCOL, GraphQLTransportWSHandler),
        (GRAPHQL_WS_PROTOCOL, GraphQLWSHandler),
    ],
)
async def test_correct_protocol(protocol, handler):
    consumer = GraphQLWSConsumer(schema=schema)
    client = WebsocketCommunicator(
        consumer,
        "/graphql",
        subprotocols=[
            protocol,
        ],
    )
    res = await client.connect()
    assert res == (True, protocol)
    assert isinstance(consumer._handler, handler)
