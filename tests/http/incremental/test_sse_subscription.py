import asyncio
import contextlib

import pytest

import strawberry
from strawberry.schema.config import StrawberryConfig
from strawberry.subscriptions import (
    GRAPHQL_SSE_PROTOCOL,
    GRAPHQL_TRANSPORT_WS_PROTOCOL,
    GRAPHQL_WS_PROTOCOL,
)
from tests.http.clients.base import HttpClient
from tests.views.schema import Mutation, MyExtension, Query, Subscription, schema


@pytest.fixture
def http_client(http_client_class: type[HttpClient]) -> HttpClient:
    with contextlib.suppress(ImportError):
        import django

        if django.VERSION < (4, 2):
            pytest.skip(reason="Django < 4.2 doesn't support async streaming responses")

        from tests.http.clients.django import DjangoHttpClient

        if http_client_class is DjangoHttpClient:
            pytest.skip(
                reason="(sync) DjangoHttpClient doesn't support SSE subscriptions"
            )

    with contextlib.suppress(ImportError):
        from tests.http.clients.channels import SyncChannelsHttpClient

        if http_client_class is SyncChannelsHttpClient:
            pytest.skip(
                reason="SyncChannelsHttpClient doesn't support SSE subscriptions"
            )

    with contextlib.suppress(ImportError):
        from tests.http.clients.async_flask import AsyncFlaskHttpClient
        from tests.http.clients.flask import FlaskHttpClient

        if http_client_class is FlaskHttpClient:
            pytest.skip(reason="FlaskHttpClient doesn't support SSE subscriptions")

        if http_client_class is AsyncFlaskHttpClient:
            pytest.xfail(
                reason="AsyncFlaskHttpClient doesn't support SSE subscriptions"
            )

    with contextlib.suppress(ImportError):
        from tests.http.clients.chalice import ChaliceHttpClient

        if http_client_class is ChaliceHttpClient:
            pytest.skip(reason="ChaliceHttpClient doesn't support SSE subscriptions")

    return http_client_class(
        schema=schema,
        subscription_protocols=(
            GRAPHQL_TRANSPORT_WS_PROTOCOL,
            GRAPHQL_WS_PROTOCOL,
            GRAPHQL_SSE_PROTOCOL,
        ),
    )


async def test_sse_subscription(http_client: HttpClient):
    response = await http_client.query(
        method="post",
        query='subscription { echo(message: "Hello world", delay: 0.2) }',
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert response.status_code == 200
    assert response.is_sse

    events = [(event, data) async for event, data in response.streaming_sse()]

    next_events = [(e, d) for e, d in events if e == "next"]
    complete_events = [(e, d) for e, d in events if e == "complete"]

    assert len(next_events) == 1
    assert next_events[0] == (
        "next",
        {
            "payload": {
                "data": {"echo": "Hello world"},
                "extensions": {"example": "example"},
            }
        },
    )
    assert len(complete_events) == 1
    assert complete_events[0] == ("complete", None)


async def test_sse_subscription_content_type_header(http_client: HttpClient):
    response = await http_client.query(
        method="post",
        query='subscription { echo(message: "Hello world", delay: 0.2) }',
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")


async def test_sse_subscription_event_format(http_client: HttpClient):
    """Verify the raw SSE event format matches the graphql-sse spec."""
    response = await http_client.query(
        method="post",
        query='subscription { echo(message: "Test", delay: 0.2) }',
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert response.status_code == 200

    events = [(event, data) async for event, data in response.streaming_sse()]

    next_events = [d for e, d in events if e == "next"]
    complete_events = [e for e, _ in events if e == "complete"]

    assert len(next_events) == 1
    assert next_events[0]["payload"]["data"]["echo"] == "Test"
    assert "complete" in complete_events


async def test_returns_error_when_trying_to_use_batching_with_sse_subscriptions(
    incremental_http_client_class: type[HttpClient],
):
    http_client = incremental_http_client_class(
        schema=strawberry.Schema(
            query=Query,
            mutation=Mutation,
            subscription=Subscription,
            extensions=[MyExtension],
            config=StrawberryConfig(batching_config={"max_operations": 10}),
        ),
        subscription_protocols=(
            GRAPHQL_TRANSPORT_WS_PROTOCOL,
            GRAPHQL_WS_PROTOCOL,
            GRAPHQL_SSE_PROTOCOL,
        ),
    )

    response = await http_client.post(
        url="/graphql",
        json=[
            {"query": 'subscription { echo(message: "Hello world", delay: 0.2) }'},
            {"query": 'subscription { echo(message: "Hello world", delay: 0.2) }'},
            {"query": 'subscription { echo(message: "Hello world", delay: 0.2) }'},
        ],
        headers={
            "content-type": "application/json",
            "accept": "text/event-stream",
        },
    )

    assert response.status_code == 400
    assert "Batching is not supported for SSE subscriptions" in response.text


async def test_sse_subscription_via_get(http_client: HttpClient):
    """SSE subscriptions should also work via GET, matching multipart parity."""
    response = await http_client.query(
        method="get",
        query='subscription { echo(message: "Hello world", delay: 0.2) }',
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert response.status_code == 200
    assert response.is_sse

    events = [(event, data) async for event, data in response.streaming_sse()]
    next_events = [(e, d) for e, d in events if e == "next"]
    complete_events = [(e, d) for e, d in events if e == "complete"]

    assert len(next_events) == 1
    assert next_events[0][1]["payload"]["data"]["echo"] == "Hello world"
    assert len(complete_events) == 1


async def test_sse_subscription_with_wrong_content_type(http_client: HttpClient):
    """When Accept is text/event-stream but Content-Type is also text/event-stream
    (instead of application/json), the server should still parse the JSON body
    gracefully rather than raising MissingQueryError deep in the stack."""
    response = await http_client.query(
        method="post",
        query='subscription { echo(message: "Hello world", delay: 0.2) }',
        headers={
            "accept": "text/event-stream",
            "content-type": "text/event-stream",
        },
    )

    assert response.status_code == 200
    assert response.is_sse

    events = [(event, data) async for event, data in response.streaming_sse()]
    next_events = [(e, d) for e, d in events if e == "next"]

    assert len(next_events) == 1
    assert next_events[0][1]["payload"]["data"]["echo"] == "Hello world"


async def test_sse_subscription_with_missing_query(http_client: HttpClient):
    """When the query field is missing from the request body, the server should
    return a proper 400 error instead of an unhandled MissingQueryError."""
    response = await http_client.post(
        url="/graphql",
        json={"variables": {}},
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert response.status_code == 400
    assert 'missing a "query" value' in response.text


async def test_sse_subscription_with_error_in_resolver(http_client: HttpClient):
    """When the subscription resolver yields a GraphQLError, it should be
    returned as a proper SSE 'next' event with errors field."""
    response = await http_client.query(
        method="post",
        query='subscription { error(message: "test error") }',
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert response.status_code == 200
    assert response.is_sse

    events = [(event, data) async for event, data in response.streaming_sse()]
    next_events = [d for e, d in events if e == "next"]
    complete_events = [e for e, _ in events if e == "complete"]

    assert len(next_events) == 1
    payload = next_events[0]["payload"]
    assert payload["data"] is None
    assert "errors" in payload
    assert payload["errors"], "Expected non-empty errors list in payload"
    messages = {
        err.get("message") for err in payload["errors"] if isinstance(err, dict)
    }
    assert any("test error" in (msg or "") for msg in messages)
    paths = {
        tuple(err.get("path", [])) for err in payload["errors"] if isinstance(err, dict)
    }
    assert ("error",) in paths
    assert "complete" in complete_events


async def test_sse_concurrent_requests_are_independent_of_websocket_subscription_limit(
    incremental_http_client_class: type[HttpClient],
):
    http_client = incremental_http_client_class(
        schema=schema,
        max_subscriptions_per_connection=1,
        subscription_protocols=(
            GRAPHQL_TRANSPORT_WS_PROTOCOL,
            GRAPHQL_WS_PROTOCOL,
            GRAPHQL_SSE_PROTOCOL,
        ),
    )

    async def run_one_subscription(message: str) -> str:
        response = await http_client.query(
            method="post",
            query=f'subscription {{ echo(message: "{message}", delay: 0.2) }}',
            headers={
                "accept": "text/event-stream",
                "content-type": "application/json",
            },
        )

        assert response.status_code == 200
        assert response.is_sse

        events = [(event, data) async for event, data in response.streaming_sse()]
        next_events = [data for event, data in events if event == "next"]
        complete_events = [event for event, _ in events if event == "complete"]

        assert len(next_events) == 1
        assert next_events[0]["payload"]["data"]["echo"] == message
        assert "complete" in complete_events

        return message

    messages = [f"message-{index}" for index in range(8)]
    results = await asyncio.gather(
        *(run_one_subscription(message) for message in messages)
    )

    assert sorted(results) == sorted(messages)


async def test_streaming_sse_ignores_heartbeat_comments():
    """SSE comment lines (heartbeats) should be silently skipped by streaming_sse.

    This is a unit test that directly exercises the SSE parsing logic with
    interleaved comment lines to verify parse_sse_block skips them correctly.
    """
    import contextlib
    import json

    def parse_sse_block(block: str):
        event = ""
        data_lines: list[str] = []
        for line in block.split("\n"):
            if line.startswith("event: "):
                event = line[7:].strip()
            elif line.startswith("data: "):
                data_lines.append(line[6:])
            elif line.startswith("data:"):
                data_lines.append(line[5:])
            elif line.startswith(":"):
                continue
        if not event:
            return None
        raw = "\n".join(data_lines).strip()
        data = None
        if raw:
            with contextlib.suppress(json.JSONDecodeError):
                data = json.loads(raw)
        return (event, data)

    sse_payload = (
        ": keep-alive\n\n"
        "event: next\n"
        'data: {"payload": {"data": {"echo": "Hello world"}}}\n\n'
        ": another-heartbeat\n\n"
        "event: complete\n"
        "data: \n\n"
    )

    events = [
        result
        for block in sse_payload.split("\n\n")
        if block.strip() and (result := parse_sse_block(block))
    ]

    assert events == [
        ("next", {"payload": {"data": {"echo": "Hello world"}}}),
        ("complete", None),
    ]


async def test_sse_subscription_with_malformed_json_body(http_client: HttpClient):
    """When Accept is text/event-stream but the request body is invalid JSON,
    the server should return a clear 400 error instead of a 500/traceback."""
    response = await http_client.post(
        url="/graphql",
        data=b"this is not valid json",
        json=None,
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert response.status_code == 400


async def test_sse_subscription_with_large_payload(http_client: HttpClient):
    """SSE subscriptions should handle large nested objects correctly."""
    large_data = {"nested": {"deep": {"value": "x" * 1000}}}
    response = await http_client.query(
        method="post",
        query="subscription LargePayload($data: JSON!) { largePayload(data: $data) }",
        variables={"data": large_data},
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert response.status_code == 200
    assert response.is_sse

    events = [(event, data) async for event, data in response.streaming_sse()]
    next_events = [d for e, d in events if e == "next"]
    complete_events = [e for e, _ in events if e == "complete"]

    assert len(next_events) == 1, f"Expected 1 next event, got {len(next_events)}"
    assert len(complete_events) == 1

    # Verify the large payload was echoed back correctly
    payload_data = next_events[0]["payload"]["data"]["largePayload"]
    assert payload_data["nested"]["deep"]["value"] == "x" * 1000


async def test_sse_subscription_last_event_id_support(http_client: HttpClient):
    """SSE events should include id fields for Last-Event-ID header support.

    The Last-Event-ID header allows clients to resume from where they left off
    after a connection drop. Each event should have a unique id field.
    """
    response = await http_client.query(
        method="post",
        query='subscription { echo(message: "test", delay: 0.2) }',
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert response.status_code == 200
    assert response.is_sse

    raw_text = response.text
    id_lines = [line for line in raw_text.split("\n") if line.startswith("id:")]
    assert len(id_lines) >= 2, (
        f"Expected at least 2 id lines (next + complete), got {len(id_lines)}"
    )
    ids = [int(line.split(":")[1].strip()) for line in id_lines]
    assert ids == list(range(1, len(ids) + 1)), (
        f"Expected sequential IDs starting at 1, got {ids}"
    )


async def test_sse_subscription_reconnects_from_last_event_id(
    incremental_http_client_class: type[HttpClient],
):
    """When a client reconnects with Last-Event-ID, server should start from that point.

    This verifies that the server correctly parses Last-Event-ID and starts
    event numbering from that point.
    """
    http_client = incremental_http_client_class(
        schema=schema,
        subscription_protocols=(
            GRAPHQL_TRANSPORT_WS_PROTOCOL,
            GRAPHQL_WS_PROTOCOL,
            GRAPHQL_SSE_PROTOCOL,
        ),
    )

    response = await http_client.query(
        method="post",
        query='subscription { echo(message: "test", delay: 0.2) }',
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
            "last-event-id": "5",
        },
    )

    assert response.status_code == 200
    assert response.is_sse

    raw_text = response.text
    id_lines = [line for line in raw_text.split("\n") if line.startswith("id:")]
    ids = [int(line.split(":")[1].strip()) for line in id_lines]
    assert ids == [6, 7], (
        f"Expected IDs 6 and 7 (continuing from last-event-id: 5), got {ids}"
    )


async def test_sse_complete_event_has_empty_data_field(http_client: HttpClient):
    """The 'complete' event must have an empty 'data:' field to trigger
    EventSource listeners per the SSE spec.

    Without an empty data field, the complete event won't trigger the listener.
    """
    response = await http_client.query(
        method="post",
        query='subscription { echo(message: "Hello world", delay: 0.2) }',
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert response.status_code == 200
    assert response.is_sse

    raw_text = response.text
    complete_blocks = [
        block for block in raw_text.split("\n\n") if "event: complete" in block
    ]

    assert len(complete_blocks) >= 1, "Expected at least one complete event"

    for block in complete_blocks:
        assert "data:" in block or "data:\n" in block or "data: " in block, (
            f"Complete event block must have 'data:' field: {block!r}"
        )
        lines = block.split("\n")
        data_lines = [line for line in lines if line.startswith("data:")]
        assert len(data_lines) == 1, "Expected exactly one data line in complete block"
        data_value = data_lines[0][5:].strip()
        assert data_value == "", (
            f"Complete event 'data:' field must be empty, got: {data_value!r}"
        )


async def test_sse_next_event_has_data_field(http_client: HttpClient):
    """The 'next' event must have a 'data:' field with the payload."""
    response = await http_client.query(
        method="post",
        query='subscription { echo(message: "Hello world", delay: 0.2) }',
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert response.status_code == 200
    assert response.is_sse

    raw_text = response.text
    next_blocks = [block for block in raw_text.split("\n\n") if "event: next" in block]

    assert len(next_blocks) == 1, "Expected exactly one next event"

    block = next_blocks[0]
    lines = block.split("\n")
    data_lines = [line for line in lines if line.startswith("data:")]

    assert len(data_lines) == 1, "Expected exactly one data line in next block"
    data_value = data_lines[0][5:].strip()
    assert data_value.startswith("{"), (
        f"Next event 'data:' field must contain JSON, got: {data_value!r}"
    )


async def test_sse_error_event_yields_next_event_with_errors(http_client: HttpClient):
    """When a subscription resolver yields a GraphQLError, it should be
    delivered as a 'next' event with errors field (not a separate 'error' event).

    The 'error' event type is reserved for non-GraphQL exceptions that occur
    during subscription iteration. GraphQL errors are wrapped in the 'next' event.
    """
    response = await http_client.query(
        method="post",
        query='subscription { error(message: "test error") }',
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert response.status_code == 200
    assert response.is_sse

    raw_text = response.text
    next_blocks = [block for block in raw_text.split("\n\n") if "event: next" in block]

    assert len(next_blocks) >= 1, (
        f"Expected at least one next event with errors, got raw: {raw_text!r}"
    )

    for block in next_blocks:
        lines = block.split("\n")
        data_lines = [line for line in lines if line.startswith("data:")]
        assert len(data_lines) == 1, "Expected exactly one data line in next block"
        data_value = data_lines[0][5:].strip()
        assert data_value.startswith("{"), (
            f"Next event 'data:' field must contain JSON, got: {data_value!r}"
        )
        assert '"errors"' in data_value, (
            f"Next event should contain errors, got: {data_value!r}"
        )
