from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import pytest

from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL
from strawberry.subscriptions.protocols.graphql_transport_ws.types import (
    CompleteMessage,
    ConnectionAckMessage,
    ConnectionInitMessage,
    NextMessage,
    SubscribeMessage,
)
from tests.views.schema import schema

if TYPE_CHECKING:
    from channels.testing import WebsocketCommunicator


@pytest.fixture
async def ws() -> AsyncGenerator[WebsocketCommunicator, None]:
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
    with (
        pytest.deprecated_call(match="Use listen_to_channel instead"),
        pytest.raises(RuntimeError, match=msg),
    ):
        await consumer.channel_listen("foobar").__anext__()

    with pytest.raises(RuntimeError, match=msg):
        async with consumer.listen_to_channel("foobar"):
            pass


@pytest.mark.django_db
async def test_channel_listen(ws: WebsocketCommunicator):
    from channels.layers import get_channel_layer

    await ws.send_json_to(ConnectionInitMessage({"type": "connection_init"}))

    connection_ack_message: ConnectionAckMessage = await ws.receive_json_from()
    assert connection_ack_message == {"type": "connection_ack"}

    await ws.send_json_to(
        SubscribeMessage(
            {
                "id": "sub1",
                "type": "subscribe",
                "payload": {
                    "query": "subscription { listener }",
                },
            }
        )
    )

    channel_layer = get_channel_layer()
    assert channel_layer

    next_message1: NextMessage = await ws.receive_json_from()
    assert "data" in next_message1["payload"]
    assert next_message1["payload"]["data"] is not None
    channel_name = next_message1["payload"]["data"]["listener"]

    await channel_layer.send(
        channel_name,
        {
            "type": "test.message",
            "text": "Hello there!",
        },
    )

    next_message2: NextMessage = await ws.receive_json_from()
    assert next_message2 == {
        "id": "sub1",
        "type": "next",
        "payload": {
            "data": {"listener": "Hello there!"},
            "extensions": {"example": "example"},
        },
    }

    await ws.send_json_to(CompleteMessage({"id": "sub1", "type": "complete"}))


@pytest.mark.django_db
async def test_channel_listen_with_confirmation(ws: WebsocketCommunicator):
    from channels.layers import get_channel_layer

    await ws.send_json_to(ConnectionInitMessage({"type": "connection_init"}))

    connection_ack_message: ConnectionAckMessage = await ws.receive_json_from()
    assert connection_ack_message == {"type": "connection_ack"}

    await ws.send_json_to(
        SubscribeMessage(
            {
                "id": "sub1",
                "type": "subscribe",
                "payload": {
                    "query": "subscription { listenerWithConfirmation }",
                },
            }
        )
    )

    channel_layer = get_channel_layer()
    assert channel_layer

    next_message1: NextMessage = await ws.receive_json_from()
    assert "data" in next_message1["payload"]
    assert next_message1["payload"]["data"] is not None
    confirmation = next_message1["payload"]["data"]["listenerWithConfirmation"]
    assert confirmation is None

    next_message2: NextMessage = await ws.receive_json_from()
    assert "data" in next_message2["payload"]
    assert next_message2["payload"]["data"] is not None
    channel_name = next_message2["payload"]["data"]["listenerWithConfirmation"]

    await channel_layer.send(
        channel_name,
        {
            "type": "test.message",
            "text": "Hello there!",
        },
    )

    next_message3: NextMessage = await ws.receive_json_from()
    assert next_message3 == {
        "id": "sub1",
        "type": "next",
        "payload": {
            "data": {"listenerWithConfirmation": "Hello there!"},
            "extensions": {"example": "example"},
        },
    }

    await ws.send_json_to(CompleteMessage({"id": "sub1", "type": "complete"}))


@pytest.mark.django_db
async def test_channel_listen_timeout(ws: WebsocketCommunicator):
    from channels.layers import get_channel_layer

    await ws.send_json_to(ConnectionInitMessage({"type": "connection_init"}))

    connection_ack_message: ConnectionAckMessage = await ws.receive_json_from()
    assert connection_ack_message == {"type": "connection_ack"}

    await ws.send_json_to(
        SubscribeMessage(
            {
                "id": "sub1",
                "type": "subscribe",
                "payload": {
                    "query": "subscription { listener(timeout: 0.5) }",
                },
            }
        )
    )

    channel_layer = get_channel_layer()
    assert channel_layer

    next_message: NextMessage = await ws.receive_json_from()
    assert "data" in next_message["payload"]
    assert next_message["payload"]["data"] is not None
    channel_name = next_message["payload"]["data"]["listener"]
    assert channel_name

    complete_message = await ws.receive_json_from()
    assert complete_message == {"id": "sub1", "type": "complete"}


@pytest.mark.django_db
async def test_channel_listen_timeout_cm(ws: WebsocketCommunicator):
    from channels.layers import get_channel_layer

    await ws.send_json_to(ConnectionInitMessage({"type": "connection_init"}))

    connection_ack_message: ConnectionAckMessage = await ws.receive_json_from()
    assert connection_ack_message == {"type": "connection_ack"}

    await ws.send_json_to(
        SubscribeMessage(
            {
                "id": "sub1",
                "type": "subscribe",
                "payload": {
                    "query": "subscription { listenerWithConfirmation(timeout: 0.5) }",
                },
            }
        )
    )

    channel_layer = get_channel_layer()
    assert channel_layer

    next_message1: NextMessage = await ws.receive_json_from()
    assert "data" in next_message1["payload"]
    assert next_message1["payload"]["data"] is not None
    confirmation = next_message1["payload"]["data"]["listenerWithConfirmation"]
    assert confirmation is None

    next_message2 = await ws.receive_json_from()
    assert "data" in next_message2["payload"]
    assert next_message2["payload"]["data"] is not None
    channel_name = next_message2["payload"]["data"]["listenerWithConfirmation"]
    assert channel_name

    complete_message: CompleteMessage = await ws.receive_json_from()
    assert complete_message == {"id": "sub1", "type": "complete"}


@pytest.mark.django_db
async def test_channel_listen_no_message_on_channel(ws: WebsocketCommunicator):
    from channels.layers import get_channel_layer

    await ws.send_json_to(ConnectionInitMessage({"type": "connection_init"}))

    connection_ack_message: ConnectionAckMessage = await ws.receive_json_from()
    assert connection_ack_message == {"type": "connection_ack"}

    await ws.send_json_to(
        SubscribeMessage(
            {
                "id": "sub1",
                "type": "subscribe",
                "payload": {
                    "query": "subscription { listener(timeout: 0.5) }",
                },
            }
        )
    )

    channel_layer = get_channel_layer()
    assert channel_layer

    next_message: NextMessage = await ws.receive_json_from()
    assert "data" in next_message["payload"]
    assert next_message["payload"]["data"] is not None
    channel_name = next_message["payload"]["data"]["listener"]
    assert channel_name

    await channel_layer.send(
        "totally-not-out-channel",
        {
            "type": "test.message",
            "text": "Hello there!",
        },
    )

    complete_message: CompleteMessage = await ws.receive_json_from()
    assert complete_message == {"id": "sub1", "type": "complete"}


@pytest.mark.django_db
async def test_channel_listen_no_message_on_channel_cm(ws: WebsocketCommunicator):
    from channels.layers import get_channel_layer

    await ws.send_json_to(ConnectionInitMessage({"type": "connection_init"}))

    connection_ack_message: ConnectionAckMessage = await ws.receive_json_from()
    assert connection_ack_message == {"type": "connection_ack"}

    await ws.send_json_to(
        SubscribeMessage(
            {
                "id": "sub1",
                "type": "subscribe",
                "payload": {
                    "query": "subscription { listenerWithConfirmation(timeout: 0.5) }",
                },
            }
        )
    )

    channel_layer = get_channel_layer()
    assert channel_layer

    next_message1: NextMessage = await ws.receive_json_from()
    assert "data" in next_message1["payload"]
    assert next_message1["payload"]["data"] is not None
    confirmation = next_message1["payload"]["data"]["listenerWithConfirmation"]
    assert confirmation is None

    next_message2 = await ws.receive_json_from()
    assert "data" in next_message2["payload"]
    assert next_message2["payload"]["data"] is not None
    channel_name = next_message2["payload"]["data"]["listenerWithConfirmation"]
    assert channel_name

    await channel_layer.send(
        "totally-not-out-channel",
        {
            "type": "test.message",
            "text": "Hello there!",
        },
    )

    complete_message: CompleteMessage = await ws.receive_json_from()
    assert complete_message == {"id": "sub1", "type": "complete"}


@pytest.mark.django_db
async def test_channel_listen_group(ws: WebsocketCommunicator):
    from channels.layers import get_channel_layer

    await ws.send_json_to(ConnectionInitMessage({"type": "connection_init"}))

    connection_ack_message: ConnectionAckMessage = await ws.receive_json_from()
    assert connection_ack_message == {"type": "connection_ack"}

    await ws.send_json_to(
        SubscribeMessage(
            {
                "id": "sub1",
                "type": "subscribe",
                "payload": {
                    "query": 'subscription { listener(group: "foobar") }',
                },
            }
        )
    )

    channel_layer = get_channel_layer()
    assert channel_layer

    next_message1 = await ws.receive_json_from()
    assert "data" in next_message1["payload"]
    assert next_message1["payload"]["data"] is not None
    channel_name = next_message1["payload"]["data"]["listener"]

    # Sent at least once to the consumer to make sure the groups were registered
    await channel_layer.send(
        channel_name,
        {
            "type": "test.message",
            "text": "Hello there!",
        },
    )

    next_message2: NextMessage = await ws.receive_json_from()
    assert next_message2 == {
        "id": "sub1",
        "type": "next",
        "payload": {
            "data": {"listener": "Hello there!"},
            "extensions": {"example": "example"},
        },
    }

    await channel_layer.group_send(
        "foobar",
        {
            "type": "test.message",
            "text": "Hello there!",
        },
    )

    next_message3: NextMessage = await ws.receive_json_from()
    assert next_message3 == {
        "id": "sub1",
        "type": "next",
        "payload": {
            "data": {"listener": "Hello there!"},
            "extensions": {"example": "example"},
        },
    }

    await ws.send_json_to(CompleteMessage({"id": "sub1", "type": "complete"}))


@pytest.mark.django_db
async def test_channel_listen_group_cm(ws: WebsocketCommunicator):
    from channels.layers import get_channel_layer

    await ws.send_json_to(ConnectionInitMessage({"type": "connection_init"}))

    connection_ack_message: ConnectionAckMessage = await ws.receive_json_from()
    assert connection_ack_message == {"type": "connection_ack"}

    await ws.send_json_to(
        SubscribeMessage(
            {
                "id": "sub1",
                "type": "subscribe",
                "payload": {
                    "query": 'subscription { listenerWithConfirmation(group: "foobar") }',
                },
            }
        )
    )

    channel_layer = get_channel_layer()
    assert channel_layer

    next_message1: NextMessage = await ws.receive_json_from()
    assert "data" in next_message1["payload"]
    assert next_message1["payload"]["data"] is not None
    confirmation = next_message1["payload"]["data"]["listenerWithConfirmation"]
    assert confirmation is None

    next_message2 = await ws.receive_json_from()
    assert "data" in next_message2["payload"]
    assert next_message2["payload"]["data"] is not None
    channel_name = next_message2["payload"]["data"]["listenerWithConfirmation"]

    # Sent at least once to the consumer to make sure the groups were registered
    await channel_layer.send(
        channel_name,
        {
            "type": "test.message",
            "text": "Hello there!",
        },
    )

    next_message3: NextMessage = await ws.receive_json_from()
    assert next_message3 == {
        "id": "sub1",
        "type": "next",
        "payload": {
            "data": {"listenerWithConfirmation": "Hello there!"},
            "extensions": {"example": "example"},
        },
    }

    await channel_layer.group_send(
        "foobar",
        {
            "type": "test.message",
            "text": "Hello there!",
        },
    )

    next_message4: NextMessage = await ws.receive_json_from()
    assert next_message4 == {
        "id": "sub1",
        "type": "next",
        "payload": {
            "data": {"listenerWithConfirmation": "Hello there!"},
            "extensions": {"example": "example"},
        },
    }

    await ws.send_json_to(CompleteMessage({"id": "sub1", "type": "complete"}))


@pytest.mark.django_db
async def test_channel_listen_group_twice(ws: WebsocketCommunicator):
    from channels.layers import get_channel_layer

    await ws.send_json_to(ConnectionInitMessage({"type": "connection_init"}))

    connection_ack_message: ConnectionAckMessage = await ws.receive_json_from()
    assert connection_ack_message == {"type": "connection_ack"}

    await ws.send_json_to(
        SubscribeMessage(
            {
                "id": "sub1",
                "type": "subscribe",
                "payload": {
                    "query": 'subscription { listener(group: "group1") }',
                },
            }
        )
    )

    await ws.send_json_to(
        SubscribeMessage(
            {
                "id": "sub2",
                "type": "subscribe",
                "payload": {
                    "query": 'subscription { listener(group: "group2") }',
                },
            }
        )
    )

    channel_layer = get_channel_layer()
    assert channel_layer

    # Wait for channel subscriptions to start
    next_message1: NextMessage = await ws.receive_json_from()
    next_message2: NextMessage = await ws.receive_json_from()
    assert {"sub1", "sub2"} == {next_message1["id"], next_message2["id"]}

    assert "data" in next_message1["payload"]
    assert next_message1["payload"]["data"] is not None
    channel_name = next_message1["payload"]["data"]["listener"]

    # Sent at least once to the consumer to make sure the groups were registered
    await channel_layer.send(
        channel_name,
        {
            "type": "test.message",
            "text": "Hello there!",
        },
    )

    next_message3: NextMessage = await ws.receive_json_from()
    next_message4: NextMessage = await ws.receive_json_from()
    assert {"sub1", "sub2"} == {next_message3["id"], next_message4["id"]}

    assert "data" in next_message3["payload"]
    assert next_message3["payload"]["data"] is not None
    assert next_message3["payload"]["data"]["listener"] == "Hello there!"

    assert "data" in next_message4["payload"]
    assert next_message4["payload"]["data"] is not None
    assert next_message4["payload"]["data"]["listener"] == "Hello there!"

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

    next_message5: NextMessage = await ws.receive_json_from()
    next_message6: NextMessage = await ws.receive_json_from()
    assert {"sub1", "sub2"} == {next_message5["id"], next_message6["id"]}

    assert "data" in next_message5["payload"]
    assert next_message5["payload"]["data"] is not None
    assert next_message5["payload"]["data"]["listener"] == "Hello group 1!"

    assert "data" in next_message6["payload"]
    assert next_message6["payload"]["data"] is not None
    assert next_message6["payload"]["data"]["listener"] == "Hello group 1!"

    await channel_layer.group_send(
        "group2",
        {
            "type": "test.message",
            "text": "Hello group 2!",
        },
    )

    next_message7: NextMessage = await ws.receive_json_from()
    next_message8: NextMessage = await ws.receive_json_from()
    assert {"sub1", "sub2"} == {next_message7["id"], next_message8["id"]}

    assert "data" in next_message7["payload"]
    assert next_message7["payload"]["data"] is not None
    assert next_message7["payload"]["data"]["listener"] == "Hello group 2!"

    assert "data" in next_message8["payload"]
    assert next_message8["payload"]["data"] is not None
    assert next_message8["payload"]["data"]["listener"] == "Hello group 2!"

    await ws.send_json_to(CompleteMessage({"id": "sub1", "type": "complete"}))
    await ws.send_json_to(CompleteMessage({"id": "sub2", "type": "complete"}))


async def test_channel_listen_group_twice_cm(ws: WebsocketCommunicator):
    from channels.layers import get_channel_layer

    await ws.send_json_to(ConnectionInitMessage({"type": "connection_init"}))

    connection_ack_message: ConnectionAckMessage = await ws.receive_json_from()
    assert connection_ack_message == {"type": "connection_ack"}

    await ws.send_json_to(
        SubscribeMessage(
            {
                "id": "sub1",
                "type": "subscribe",
                "payload": {
                    "query": 'subscription { listenerWithConfirmation(group: "group1") }',
                },
            }
        )
    )

    await ws.send_json_to(
        SubscribeMessage(
            {
                "id": "sub2",
                "type": "subscribe",
                "payload": {
                    "query": 'subscription { listenerWithConfirmation(group: "group2") }',
                },
            }
        )
    )

    channel_layer = get_channel_layer()
    assert channel_layer

    # Wait for confirmation for channel subscriptions
    messages = await asyncio.gather(
        ws.receive_json_from(),
        ws.receive_json_from(),
        ws.receive_json_from(),
        ws.receive_json_from(),
    )
    confirmation1 = next(
        i
        for i in messages
        if not i["payload"]["data"]["listenerWithConfirmation"] and i["id"] == "sub1"
    )
    confirmation2 = next(
        i
        for i in messages
        if not i["payload"]["data"]["listenerWithConfirmation"] and i["id"] == "sub2"
    )
    channel_name1 = next(
        i
        for i in messages
        if i["payload"]["data"]["listenerWithConfirmation"] and i["id"] == "sub1"
    )
    channel_name2 = next(
        i
        for i in messages
        if i["payload"]["data"]["listenerWithConfirmation"] and i["id"] == "sub2"
    )

    # Ensure correct ordering of responses
    assert messages.index(confirmation1) < messages.index(channel_name1)
    assert messages.index(confirmation2) < messages.index(channel_name2)
    channel_name = channel_name1["payload"]["data"]["listenerWithConfirmation"]

    # Sent at least once to the consumer to make sure the groups were registered
    await channel_layer.send(
        channel_name,
        {
            "type": "test.message",
            "text": "Hello there!",
        },
    )

    next_message1: NextMessage = await ws.receive_json_from()
    next_message2: NextMessage = await ws.receive_json_from()
    assert {"sub1", "sub2"} == {next_message1["id"], next_message2["id"]}

    assert "data" in next_message1["payload"]
    assert next_message1["payload"]["data"] is not None
    assert (
        next_message1["payload"]["data"]["listenerWithConfirmation"] == "Hello there!"
    )

    assert "data" in next_message2["payload"]
    assert next_message2["payload"]["data"] is not None
    assert (
        next_message2["payload"]["data"]["listenerWithConfirmation"] == "Hello there!"
    )

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

    next_message3: NextMessage = await ws.receive_json_from()
    next_message4: NextMessage = await ws.receive_json_from()
    assert {"sub1", "sub2"} == {next_message3["id"], next_message4["id"]}

    assert "data" in next_message3["payload"]
    assert next_message3["payload"]["data"] is not None
    assert (
        next_message3["payload"]["data"]["listenerWithConfirmation"] == "Hello group 1!"
    )

    assert "data" in next_message4["payload"]
    assert next_message4["payload"]["data"] is not None
    assert (
        next_message4["payload"]["data"]["listenerWithConfirmation"] == "Hello group 1!"
    )

    await channel_layer.group_send(
        "group2",
        {
            "type": "test.message",
            "text": "Hello group 2!",
        },
    )

    next_message5: NextMessage = await ws.receive_json_from()
    next_message6: NextMessage = await ws.receive_json_from()
    assert {"sub1", "sub2"} == {next_message5["id"], next_message6["id"]}

    assert "data" in next_message5["payload"]
    assert next_message5["payload"]["data"] is not None
    assert (
        next_message5["payload"]["data"]["listenerWithConfirmation"] == "Hello group 2!"
    )

    assert "data" in next_message6["payload"]
    assert next_message6["payload"]["data"] is not None
    assert (
        next_message6["payload"]["data"]["listenerWithConfirmation"] == "Hello group 2!"
    )

    await ws.send_json_to(CompleteMessage({"id": "sub1", "type": "complete"}))
    await ws.send_json_to(CompleteMessage({"id": "sub2", "type": "complete"}))
