import json
from collections.abc import AsyncGenerator

from strawberry.http.base import BaseView
from strawberry.http.streaming import (
    MultipartSubscriptionTransport,
    MultipartTransport,
)
from strawberry.subscriptions import MULTIPART_SUBSCRIPTION_PROTOCOL


def test_multipart_transport_encode_multipart_data_uses_utf8_byte_length() -> None:
    encoded_json = json.dumps({"value": "\u00e9"}, ensure_ascii=False)
    transport = MultipartTransport()

    data = transport.encode_multipart_data({"value": "\u00e9"}, lambda _: encoded_json)

    assert f"Content-Length: {len(encoded_json.encode())}\r\n" in data


async def test_multipart_transport_streams_data() -> None:
    transport = MultipartTransport()

    async def data() -> AsyncGenerator[object, None]:
        yield {"data": {"ok": True}}

    stream = transport.stream(data, json.dumps)

    result = [chunk async for chunk in stream()]

    assert transport.headers == {"Content-Type": 'multipart/mixed; boundary="-"'}
    assert result[0] == "---"
    assert '"data": {"ok": true}' in result[1]
    assert result[-1] == "--\r\n"


def test_multipart_subscription_transport_accepts_content_type() -> None:
    transport = MultipartSubscriptionTransport()

    assert transport.accepts_content_type(
        "multipart/mixed",
        {"boundary": "graphql", "subscriptionspec": "1.0,application/json"},
    )
    assert transport.accepts_content_type(
        "multipart/mixed",
        {"subscriptionspec": '"1.0",application/json'},
    )
    assert not transport.accepts_content_type(
        "multipart/mixed",
        {"boundary": "other", "subscriptionspec": "1.0,application/json"},
    )
    assert not transport.accepts_content_type(
        "application/json",
        {"subscriptionspec": "1.0,application/json"},
    )


def test_multipart_subscription_transport_accepts_header() -> None:
    transport = MultipartSubscriptionTransport()

    assert transport.accepts(
        "multipart/mixed;boundary=graphql;subscriptionSpec=1.0,application/json"
    )


def test_multipart_subscription_transport_encodes_messages() -> None:
    transport = MultipartSubscriptionTransport(separator="custom")

    next_message = transport.encode_next({"data": {"ok": True}}, json.dumps)
    heartbeat_message = transport.heartbeat_message(json.dumps)

    assert transport.headers == {
        "Content-Type": "multipart/mixed;boundary=custom;subscriptionSpec=1.0,application/json"
    }
    assert '"payload": {"data": {"ok": true}}' in next_message
    assert next_message.endswith("\r\n--custom")
    assert heartbeat_message.endswith("{}\r\n--custom")
    assert transport.encode_complete() == "\r\n--custom--\r\n"


def test_base_view_caches_stream_transport_map() -> None:
    class MockTransport(MultipartSubscriptionTransport):
        calls = 0

        def __init__(self) -> None:
            super().__init__()
            type(self).calls += 1

    class MockView(BaseView[object]):
        protocols = (MULTIPART_SUBSCRIPTION_PROTOCOL,)
        stream_transport_classes_by_protocol = {
            MULTIPART_SUBSCRIPTION_PROTOCOL: MockTransport,
        }

    view = MockView()

    transport = view._get_stream_transport("multipart-subscription")

    assert transport is view._get_stream_transport_from_headers(
        {
            "Accept": (
                "multipart/mixed;boundary=graphql;subscriptionSpec=1.0,application/json"
            )
        }
    )
    assert transport is view._get_stream_transport_from_content_type(
        "multipart/mixed",
        {"boundary": "graphql", "subscriptionspec": "1.0,application/json"},
    )
    assert MockTransport.calls == 1


def test_base_view_only_instantiates_enabled_stream_transports() -> None:
    class MockTransport(MultipartSubscriptionTransport):
        calls = 0

        def __init__(self) -> None:
            super().__init__()
            type(self).calls += 1

    class MockView(BaseView[object]):
        stream_transport_classes_by_protocol = {
            MULTIPART_SUBSCRIPTION_PROTOCOL: MockTransport,
        }

    view = MockView()

    assert view._get_stream_transport("multipart-subscription") is None
    assert (
        view._get_stream_transport_from_headers(
            {
                "Accept": (
                    "multipart/mixed;boundary=graphql;subscriptionSpec=1.0,application/json"
                )
            }
        )
        is None
    )
    assert MockTransport.calls == 0
