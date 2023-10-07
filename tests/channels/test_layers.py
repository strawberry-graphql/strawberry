from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Generator

import pytest

from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL
from strawberry.subscriptions.protocols.graphql_transport_ws.types import (
    CompleteMessage,
    ConnectionAckMessage,
    ConnectionInitMessage,
    NextMessage,
    SubscribeMessage,
    SubscribeMessagePayload,
)
from tests.views.schema import schema

if TYPE_CHECKING:
    from channels.testing import WebsocketCommunicator


@pytest.fixture
async def ws() -> Generator[WebsocketCommunicator, None, None]:
    from channels.testing import WebsocketCommunicator
    from strawberry.channels import GraphQLWSConsumer

    client = WebsocketCommunicator(
        GraphQLWSConsumer.as_asgi(schema=schema),
        "/graphql",
        subprotocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL],
    )
    res = await client.connect()
    assert res == (True, GRAPHQL_TRANSPORT_WS_PROTOCOL)

    yield client

    await client.disconnect()


async def test_no_layers():
    from strawberry.channels.handlers.base import ChannelsConsumer

    consumer = ChannelsConsumer()
    # Mimic lack of layers. If layers is not installed/configured in channels,
    # consumer.channel_layer will be `None`
    consumer.channel_layer = None

    msg = (
        "Layers integration is required listening for channels.\n"
        "Check https://channels.readthedocs.io/en/stable/topics/channel_layers.html "
        "for more information"
    )
    with pytest.raises(RuntimeError, match=msg):
        await consumer.channel_listen("foobar").__anext__()

    with pytest.raises(RuntimeError, match=msg):
        async with consumer.listen_to_channel("foobar"):
            pass


async def test_channel_listen(ws: WebsocketCommunicator):
    from channels.layers import get_channel_layer

    await ws.send_json_to(ConnectionInitMessage().as_dict())

    response = await ws.receive_json_from()
    assert response == ConnectionAckMessage().as_dict()

    await ws.send_json_to(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(
                query="subscription { listener }",
            ),
        ).as_dict()
    )

    channel_layer = get_channel_layer()
    assert channel_layer

    response = await ws.receive_json_from()
    channel_name = response["payload"]["data"]["listener"]

    await channel_layer.send(
        channel_name,
        {
            "type": "test.message",
            "text": "Hello there!",
        },
    )

    response = await ws.receive_json_from()
    assert (
        response
        == NextMessage(
            id="sub1", payload={"data": {"listener": "Hello there!"}}
        ).as_dict()
    )

    await ws.send_json_to(CompleteMessage(id="sub1").as_dict())


async def test_channel_listen_with_confirmation(ws: WebsocketCommunicator):
    from channels.layers import get_channel_layer

    await ws.send_json_to(ConnectionInitMessage().as_dict())

    response = await ws.receive_json_from()
    assert response == ConnectionAckMessage().as_dict()

    await ws.send_json_to(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(
                query="subscription { listenerWithConfirmation }",
            ),
        ).as_dict()
    )

    channel_layer = get_channel_layer()
    assert channel_layer

    response = await ws.receive_json_from()
    confirmation = response["payload"]["data"]["listenerWithConfirmation"]
    assert confirmation is None

    response = await ws.receive_json_from()
    channel_name = response["payload"]["data"]["listenerWithConfirmation"]

    await channel_layer.send(
        channel_name,
        {
            "type": "test.message",
            "text": "Hello there!",
        },
    )

    response = await ws.receive_json_from()
    assert (
        response
        == NextMessage(
            id="sub1", payload={"data": {"listenerWithConfirmation": "Hello there!"}}
        ).as_dict()
    )

    await ws.send_json_to(CompleteMessage(id="sub1").as_dict())


async def test_channel_listen_timeout(ws: WebsocketCommunicator):
    from channels.layers import get_channel_layer

    await ws.send_json_to(ConnectionInitMessage().as_dict())

    response = await ws.receive_json_from()
    assert response == ConnectionAckMessage().as_dict()

    await ws.send_json_to(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(
                query="subscription { listener(timeout: 0.5) }",
            ),
        ).as_dict()
    )

    channel_layer = get_channel_layer()
    assert channel_layer

    response = await ws.receive_json_from()
    channel_name = response["payload"]["data"]["listener"]
    assert channel_name

    response = await ws.receive_json_from()
    assert response == CompleteMessage(id="sub1").as_dict()


async def test_channel_listen_timeout_cm(ws: WebsocketCommunicator):
    from channels.layers import get_channel_layer

    await ws.send_json_to(ConnectionInitMessage().as_dict())

    response = await ws.receive_json_from()
    assert response == ConnectionAckMessage().as_dict()

    await ws.send_json_to(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(
                query="subscription { listenerWithConfirmation(timeout: 0.5) }",
            ),
        ).as_dict()
    )

    channel_layer = get_channel_layer()
    assert channel_layer

    response = await ws.receive_json_from()
    confirmation = response["payload"]["data"]["listenerWithConfirmation"]
    assert confirmation is None

    response = await ws.receive_json_from()
    channel_name = response["payload"]["data"]["listenerWithConfirmation"]
    assert channel_name

    response = await ws.receive_json_from()
    assert response == CompleteMessage(id="sub1").as_dict()


async def test_channel_listen_no_message_on_channel(ws: WebsocketCommunicator):
    from channels.layers import get_channel_layer

    await ws.send_json_to(ConnectionInitMessage().as_dict())

    response = await ws.receive_json_from()
    assert response == ConnectionAckMessage().as_dict()

    await ws.send_json_to(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(
                query="subscription { listener(timeout: 0.5) }",
            ),
        ).as_dict()
    )

    channel_layer = get_channel_layer()
    assert channel_layer

    response = await ws.receive_json_from()
    channel_name = response["payload"]["data"]["listener"]
    assert channel_name

    await channel_layer.send(
        "totally-not-out-channel",
        {
            "type": "test.message",
            "text": "Hello there!",
        },
    )

    response = await ws.receive_json_from()
    assert response == CompleteMessage(id="sub1").as_dict()


async def test_channel_listen_no_message_on_channel_cm(ws: WebsocketCommunicator):
    from channels.layers import get_channel_layer

    await ws.send_json_to(ConnectionInitMessage().as_dict())

    response = await ws.receive_json_from()
    assert response == ConnectionAckMessage().as_dict()

    await ws.send_json_to(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(
                query="subscription { listenerWithConfirmation(timeout: 0.5) }",
            ),
        ).as_dict()
    )

    channel_layer = get_channel_layer()
    assert channel_layer

    response = await ws.receive_json_from()
    confirmation = response["payload"]["data"]["listenerWithConfirmation"]
    assert confirmation is None

    response = await ws.receive_json_from()
    channel_name = response["payload"]["data"]["listenerWithConfirmation"]
    assert channel_name

    await channel_layer.send(
        "totally-not-out-channel",
        {
            "type": "test.message",
            "text": "Hello there!",
        },
    )

    response = await ws.receive_json_from()
    assert response == CompleteMessage(id="sub1").as_dict()


async def test_channel_listen_group(ws: WebsocketCommunicator):
    from channels.layers import get_channel_layer

    await ws.send_json_to(ConnectionInitMessage().as_dict())

    response = await ws.receive_json_from()
    assert response == ConnectionAckMessage().as_dict()

    await ws.send_json_to(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(
                query='subscription { listener(group: "foobar") }',
            ),
        ).as_dict()
    )

    channel_layer = get_channel_layer()
    assert channel_layer

    response = await ws.receive_json_from()
    channel_name = response["payload"]["data"]["listener"]

    # Sent at least once to the consumer to make sure the groups were registered
    await channel_layer.send(
        channel_name,
        {
            "type": "test.message",
            "text": "Hello there!",
        },
    )
    response = await ws.receive_json_from()
    assert (
        response
        == NextMessage(
            id="sub1", payload={"data": {"listener": "Hello there!"}}
        ).as_dict()
    )

    await channel_layer.group_send(
        "foobar",
        {
            "type": "test.message",
            "text": "Hello there!",
        },
    )

    response = await ws.receive_json_from()
    assert (
        response
        == NextMessage(
            id="sub1", payload={"data": {"listener": "Hello there!"}}
        ).as_dict()
    )

    await ws.send_json_to(CompleteMessage(id="sub1").as_dict())


async def test_channel_listen_group_cm(ws: WebsocketCommunicator):
    from channels.layers import get_channel_layer

    await ws.send_json_to(ConnectionInitMessage().as_dict())

    response = await ws.receive_json_from()
    assert response == ConnectionAckMessage().as_dict()

    await ws.send_json_to(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(
                query='subscription { listenerWithConfirmation(group: "foobar") }',
            ),
        ).as_dict()
    )

    channel_layer = get_channel_layer()
    assert channel_layer

    response = await ws.receive_json_from()
    confirmation = response["payload"]["data"]["listenerWithConfirmation"]
    assert confirmation is None

    response = await ws.receive_json_from()
    channel_name = response["payload"]["data"]["listenerWithConfirmation"]

    # Sent at least once to the consumer to make sure the groups were registered
    await channel_layer.send(
        channel_name,
        {
            "type": "test.message",
            "text": "Hello there!",
        },
    )
    response = await ws.receive_json_from()
    assert (
        response
        == NextMessage(
            id="sub1", payload={"data": {"listenerWithConfirmation": "Hello there!"}}
        ).as_dict()
    )

    await channel_layer.group_send(
        "foobar",
        {
            "type": "test.message",
            "text": "Hello there!",
        },
    )

    response = await ws.receive_json_from()
    assert (
        response
        == NextMessage(
            id="sub1", payload={"data": {"listenerWithConfirmation": "Hello there!"}}
        ).as_dict()
    )

    await ws.send_json_to(CompleteMessage(id="sub1").as_dict())


async def test_channel_listen_group_twice(ws: WebsocketCommunicator):
    from channels.layers import get_channel_layer

    await ws.send_json_to(ConnectionInitMessage().as_dict())

    response = await ws.receive_json_from()
    assert response == ConnectionAckMessage().as_dict()

    await ws.send_json_to(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(
                query='subscription { listener(group: "group1") }',
            ),
        ).as_dict()
    )

    await ws.send_json_to(
        SubscribeMessage(
            id="sub2",
            payload=SubscribeMessagePayload(
                query='subscription { listener(group: "group2") }',
            ),
        ).as_dict()
    )

    channel_layer = get_channel_layer()
    assert channel_layer

    # Wait for channel subscriptions to start
    response1, response2 = await asyncio.gather(
        ws.receive_json_from(), ws.receive_json_from()
    )
    assert {"sub1", "sub2"} == {response1["id"], response2["id"]}
    channel_name = response1["payload"]["data"]["listener"]

    # Sent at least once to the consumer to make sure the groups were registered
    await channel_layer.send(
        channel_name,
        {
            "type": "test.message",
            "text": "Hello there!",
        },
    )
    response1, response2 = await asyncio.gather(
        ws.receive_json_from(), ws.receive_json_from()
    )
    assert {"sub1", "sub2"} == {response1["id"], response2["id"]}
    assert response1["payload"]["data"]["listener"] == "Hello there!"
    assert response2["payload"]["data"]["listener"] == "Hello there!"

    # We now have two channel_listen AsyncGenerators waiting, one for id="sub1"
    # and one for id="sub2". This group message will be received by both of them
    # as they are both running on the same ChannelsConsumer instance so even
    # though "sub2" was initialised with "group2" as the argument, it will receive
    # this message for "group1"
    await channel_layer.group_send(
        "group1",
        {
            "type": "test.message",
            "text": "Hello group 1!",
        },
    )

    response1, response2 = await asyncio.gather(
        ws.receive_json_from(), ws.receive_json_from()
    )
    assert {"sub1", "sub2"} == {response1["id"], response2["id"]}
    assert response1["payload"]["data"]["listener"] == "Hello group 1!"
    assert response2["payload"]["data"]["listener"] == "Hello group 1!"

    await channel_layer.group_send(
        "group2",
        {
            "type": "test.message",
            "text": "Hello group 2!",
        },
    )

    response1, response2 = await asyncio.gather(
        ws.receive_json_from(), ws.receive_json_from()
    )
    assert {"sub1", "sub2"} == {response1["id"], response2["id"]}
    assert response1["payload"]["data"]["listener"] == "Hello group 2!"
    assert response2["payload"]["data"]["listener"] == "Hello group 2!"

    await ws.send_json_to(CompleteMessage(id="sub1").as_dict())
    await ws.send_json_to(CompleteMessage(id="sub2").as_dict())


async def test_channel_listen_group_twice_cm(ws: WebsocketCommunicator):
    from channels.layers import get_channel_layer

    await ws.send_json_to(ConnectionInitMessage().as_dict())

    response = await ws.receive_json_from()
    assert response == ConnectionAckMessage().as_dict()

    await ws.send_json_to(
        SubscribeMessage(
            id="sub1",
            payload=SubscribeMessagePayload(
                query='subscription { listenerWithConfirmation(group: "group1") }',
            ),
        ).as_dict()
    )

    await ws.send_json_to(
        SubscribeMessage(
            id="sub2",
            payload=SubscribeMessagePayload(
                query='subscription { listenerWithConfirmation(group: "group2") }',
            ),
        ).as_dict()
    )

    channel_layer = get_channel_layer()
    assert channel_layer

    # Wait for confirmation for channel subscriptions
    responses = await asyncio.gather(
        ws.receive_json_from(),
        ws.receive_json_from(),
        ws.receive_json_from(),
        ws.receive_json_from(),
    )
    confirmation1 = next(
        i
        for i in responses
        if not i["payload"]["data"]["listenerWithConfirmation"] and i["id"] == "sub1"
    )
    confirmation2 = next(
        i
        for i in responses
        if not i["payload"]["data"]["listenerWithConfirmation"] and i["id"] == "sub2"
    )
    channel_name1 = next(
        i
        for i in responses
        if i["payload"]["data"]["listenerWithConfirmation"] and i["id"] == "sub1"
    )
    channel_name2 = next(
        i
        for i in responses
        if i["payload"]["data"]["listenerWithConfirmation"] and i["id"] == "sub2"
    )
    # Ensure correct ordering of responses
    assert responses.index(confirmation1) < responses.index(channel_name1)
    assert responses.index(confirmation2) < responses.index(channel_name2)
    channel_name = channel_name1["payload"]["data"]["listenerWithConfirmation"]

    # Sent at least once to the consumer to make sure the groups were registered
    await channel_layer.send(
        channel_name,
        {
            "type": "test.message",
            "text": "Hello there!",
        },
    )
    response1, response2 = await asyncio.gather(
        ws.receive_json_from(), ws.receive_json_from()
    )
    assert {"sub1", "sub2"} == {response1["id"], response2["id"]}
    assert response1["payload"]["data"]["listenerWithConfirmation"] == "Hello there!"
    assert response2["payload"]["data"]["listenerWithConfirmation"] == "Hello there!"

    # We now have two channel_listen AsyncGenerators waiting, one for id="sub1"
    # and one for id="sub2". This group message will be received by both of them
    # as they are both running on the same ChannelsConsumer instance so even
    # though "sub2" was initialised with "group2" as the argument, it will receive
    # this message for "group1"
    await channel_layer.group_send(
        "group1",
        {
            "type": "test.message",
            "text": "Hello group 1!",
        },
    )

    response1, response2 = await asyncio.gather(
        ws.receive_json_from(), ws.receive_json_from()
    )
    assert {"sub1", "sub2"} == {response1["id"], response2["id"]}
    assert response1["payload"]["data"]["listenerWithConfirmation"] == "Hello group 1!"
    assert response2["payload"]["data"]["listenerWithConfirmation"] == "Hello group 1!"

    await channel_layer.group_send(
        "group2",
        {
            "type": "test.message",
            "text": "Hello group 2!",
        },
    )

    response1, response2 = await asyncio.gather(
        ws.receive_json_from(), ws.receive_json_from()
    )
    assert {"sub1", "sub2"} == {response1["id"], response2["id"]}
    assert response1["payload"]["data"]["listenerWithConfirmation"] == "Hello group 2!"
    assert response2["payload"]["data"]["listenerWithConfirmation"] == "Hello group 2!"

    await ws.send_json_to(CompleteMessage(id="sub1").as_dict())
    await ws.send_json_to(CompleteMessage(id="sub2").as_dict())
