from typing import Union

import pytest

from channels.testing.websocket import WebsocketCommunicator
from strawberry.channels.handlers.graphql_transport_ws_handler import (
    GraphQLTransportWSHandler,
)
from strawberry.channels.handlers.graphql_ws_handler import GraphQLWSHandler
from strawberry.channels.handlers.ws_handler import GraphQLWSConsumer
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL
from tests.http.schema import get_schema


async def test_wrong_protocol():
    GraphQLWSConsumer.as_asgi(schema=get_schema())
    client = WebsocketCommunicator(
        GraphQLWSConsumer.as_asgi(schema=get_schema()),
        "/graphql",
        subprotocols=[
            "non-existing",
        ],
    )
    res = await client.connect()
    assert res == (False, 4406)


@pytest.mark.parametrize(
    ("protocol", "handler"),
    [
        (GRAPHQL_TRANSPORT_WS_PROTOCOL, GraphQLTransportWSHandler),
        (GRAPHQL_WS_PROTOCOL, GraphQLWSHandler),
    ],
)
async def test_correct_protocol(
    protocol: str, handler: Union[GraphQLTransportWSHandler, GraphQLWSHandler]
):
    consumer = GraphQLWSConsumer(schema=get_schema())
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
