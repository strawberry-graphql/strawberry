from strawberry.channels.context import StrawberryChannelsContext
from strawberry.channels.handlers.base import ChannelsConsumer


def test_getitem():
    consumer = ChannelsConsumer()
    ctx = StrawberryChannelsContext(request=consumer)
    assert ctx["request"] is consumer


def test_get():
    consumer = ChannelsConsumer()
    ctx = StrawberryChannelsContext(request=consumer)
    assert ctx.get("request") is consumer
