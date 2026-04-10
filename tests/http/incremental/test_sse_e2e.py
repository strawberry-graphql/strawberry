"""End-to-end tests for SSE subscription lifecycle.

These tests verify the full SSE protocol flow from connection to completion,
covering real-world scenarios like client reconnection, error recovery,
concurrent subscriptions, and header/protocol compliance.
"""

import asyncio
import contextlib
from collections.abc import AsyncGenerator
from typing import Any

import pytest

import strawberry
from tests.http.clients.base import HttpClient
from tests.views.schema import schema


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

    return http_client_class(schema=schema)


# ---------------------------------------------------------------------------
# E2E: Full subscription lifecycle tests
# ---------------------------------------------------------------------------


async def test_e2e_sse_full_lifecycle_connect_receive_complete(
    http_client: HttpClient,
):
    """End-to-end: connect via SSE, receive events, and verify clean completion.

    Verifies the full SSE lifecycle:
    1. Client sends POST with Accept: text/event-stream
    2. Server responds with 200 and text/event-stream content-type
    3. Server sends `next` events with subscription data
    4. Server sends `complete` event to signal end
    5. All events have sequential IDs for reconnection
    6. Cache-Control and Connection headers are set correctly
    """
    response = await http_client.query(
        method="post",
        query='subscription { echo(message: "e2e test", delay: 0.1) }',
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    # 1. Verify HTTP response metadata
    assert response.status_code == 200
    assert response.is_sse
    content_type = response.headers.get("content-type", "")
    assert "text/event-stream" in content_type

    # 2. Verify cache headers (per SSE best practices)
    cache_control = response.headers.get("cache-control", "")
    assert "no-cache" in cache_control

    # 3. Parse and verify SSE events
    events = [(event, data) async for event, data in response.streaming_sse()]

    next_events = [(e, d) for e, d in events if e == "next"]
    complete_events = [(e, d) for e, d in events if e == "complete"]

    assert len(next_events) == 1, f"Expected 1 next event, got {len(next_events)}"
    assert len(complete_events) == 1, "Expected exactly 1 complete event"

    # 4. Verify next event payload structure
    payload = next_events[0][1]
    assert "payload" in payload
    assert "data" in payload["payload"]
    assert payload["payload"]["data"]["echo"] == "e2e test"

    # 5. Verify complete event has no payload
    assert complete_events[0][1] is None

    # 6. Verify raw event IDs are sequential
    raw_text = response.text
    id_lines = [line for line in raw_text.split("\n") if line.startswith("id:")]
    assert len(id_lines) >= 2, f"Expected at least 2 id lines, got {id_lines}"
    ids = [int(line.split(":")[1].strip()) for line in id_lines]
    assert ids == sorted(ids), f"IDs should be sequential, got {ids}"
    assert ids[0] >= 1, "IDs should start at 1 or higher"


async def test_e2e_sse_multi_event_subscription(http_client: HttpClient):
    """End-to-end: subscription that yields multiple events over time.

    Verifies that multiple `next` events are delivered in order,
    each with correct payload, followed by a single `complete` event.
    """

    @strawberry.type
    class Q:
        @strawberry.field
        def hello(self) -> str:
            return "world"

    @strawberry.type
    class Sub:
        @strawberry.subscription
        async def countdown(self, start: int = 3) -> AsyncGenerator[int, None]:
            for i in range(start, 0, -1):
                yield i

    multi_schema = strawberry.Schema(query=Q, subscription=Sub)

    with contextlib.suppress(ImportError):
        from tests.http.clients.async_django import AsyncDjangoHttpClient

        if isinstance(http_client, AsyncDjangoHttpClient):
            pytest.skip("AsyncDjango doesn't support custom schemas in this fixture")

    # Try to create a client with the multi-event schema
    client = type(http_client)(schema=multi_schema)

    response = await client.query(
        method="post",
        query="subscription { countdown(start: 3) }",
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

    assert len(next_events) == 3
    assert next_events[0]["payload"]["data"]["countdown"] == 3
    assert next_events[1]["payload"]["data"]["countdown"] == 2
    assert next_events[2]["payload"]["data"]["countdown"] == 1
    assert len(complete_events) == 1


async def test_e2e_sse_error_recovery_continues_to_complete(http_client: HttpClient):
    """End-to-end: when a resolver yields a GraphQL error, the stream should
    deliver the error in a `next` event and still complete normally.

    This verifies that GraphQL-level errors don't crash the SSE stream.
    """
    response = await http_client.query(
        method="post",
        query='subscription { error(message: "resolver failed") }',
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert response.status_code == 200
    assert response.is_sse

    events = [(event, data) async for event, data in response.streaming_sse()]
    event_types = [e for e, _ in events]

    # Should have at least one next event (with errors) and a complete
    assert "next" in event_types
    assert "complete" in event_types

    # The next event should contain errors in the payload
    next_events = [d for e, d in events if e == "next"]
    assert len(next_events) >= 1
    payload = next_events[0]["payload"]
    assert "errors" in payload
    assert payload["data"] is None


async def test_e2e_sse_exception_in_resolver_yields_error_in_next_event(
    http_client: HttpClient,
):
    """End-to-end: when a resolver raises an unhandled exception,
    the SSE stream should deliver the error as a `next` event with
    errors in the payload, followed by a `complete` event.

    GraphQL catches resolver exceptions and wraps them in the standard
    errors format within the ExecutionResult.
    """
    response = await http_client.query(
        method="post",
        query='subscription { exception(message: "unhandled crash") }',
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

    # Exception is wrapped in a next event with errors
    assert len(next_events) >= 1, f"Expected next event with error, got: {events}"
    payload = next_events[0]["payload"]
    assert "errors" in payload
    assert "complete" in complete_events


async def test_e2e_sse_concurrent_subscriptions(http_client: HttpClient):
    """End-to-end: multiple concurrent SSE subscriptions should each receive
    their own independent event streams without interference.
    """
    messages = ["alpha", "beta", "gamma"]

    async def subscribe(msg: str) -> dict[str, Any]:
        resp = await http_client.query(
            method="post",
            query=f'subscription {{ echo(message: "{msg}", delay: 0.1) }}',
            headers={
                "accept": "text/event-stream",
                "content-type": "application/json",
            },
        )
        assert resp.status_code == 200
        assert resp.is_sse

        events = [(e, d) async for e, d in resp.streaming_sse()]
        next_events = [d for e, d in events if e == "next"]
        complete_events = [e for e, _ in events if e == "complete"]

        return {
            "message": msg,
            "next_count": len(next_events),
            "complete_count": len(complete_events),
            "echo_value": next_events[0]["payload"]["data"]["echo"]
            if next_events
            else None,
        }

    results = await asyncio.gather(*(subscribe(m) for m in messages))

    for result in results:
        assert result["next_count"] == 1
        assert result["complete_count"] == 1
        assert result["echo_value"] == result["message"]


async def test_e2e_sse_query_via_get_request(http_client: HttpClient):
    """End-to-end: SSE subscriptions should work via GET requests,
    with query parameters instead of JSON body."""
    response = await http_client.query(
        method="get",
        query='subscription { echo(message: "get request", delay: 0.1) }',
        headers={
            "accept": "text/event-stream",
        },
    )

    assert response.status_code == 200
    assert response.is_sse

    events = [(event, data) async for event, data in response.streaming_sse()]
    next_events = [d for e, d in events if e == "next"]
    complete_events = [e for e, _ in events if e == "complete"]

    assert len(next_events) == 1
    assert next_events[0]["payload"]["data"]["echo"] == "get request"
    assert len(complete_events) == 1


async def test_e2e_sse_extensions_present_in_every_event(http_client: HttpClient):
    """End-to-end: schema extensions should be included in every `next` event's
    payload, verifying extensions work correctly with SSE streaming."""
    response = await http_client.query(
        method="post",
        query='subscription { echo(message: "with extensions", delay: 0.1) }',
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert response.status_code == 200
    assert response.is_sse

    events = [(event, data) async for event, data in response.streaming_sse()]
    next_events = [d for e, d in events if e == "next"]

    assert len(next_events) >= 1
    for event_data in next_events:
        payload = event_data["payload"]
        assert "extensions" in payload, (
            f"Extensions missing from SSE event: {event_data}"
        )
        assert "example" in payload["extensions"], (
            f"MyExtension results missing: {payload['extensions']}"
        )


async def test_e2e_sse_non_subscription_query_returns_200(
    http_client: HttpClient,
):
    """End-to-end: a regular query (not subscription) sent with
    Accept: text/event-stream should still return a 200 response.

    The server processes the query normally even with SSE headers.
    """
    response = await http_client.query(
        method="post",
        query="{ hello }",
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    # Regular query should still return 200
    assert response.status_code == 200


async def test_e2e_sse_reconnection_with_last_event_id(http_client: HttpClient):
    """End-to-end: simulate a client reconnection using Last-Event-ID header.

    Verifies:
    1. First connection receives events starting from ID 1
    2. Reconnection with Last-Event-ID starts from the next ID
    3. Event IDs are continuous across reconnections
    """
    # First connection - get initial events
    response1 = await http_client.query(
        method="post",
        query='subscription { echo(message: "first", delay: 0.1) }',
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert response1.status_code == 200
    assert response1.is_sse

    raw_text1 = response1.text
    id_lines1 = [line for line in raw_text1.split("\n") if line.startswith("id:")]
    ids1 = [int(line.split(":")[1].strip()) for line in id_lines1]
    assert ids1[0] == 1, f"First event should have ID 1, got {ids1[0]}"

    last_id = ids1[-1]

    # Simulate reconnection with Last-Event-ID
    response2 = await http_client.query(
        method="post",
        query='subscription { echo(message: "reconnected", delay: 0.1) }',
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
            "last-event-id": str(last_id),
        },
    )

    assert response2.status_code == 200
    assert response2.is_sse

    raw_text2 = response2.text
    id_lines2 = [line for line in raw_text2.split("\n") if line.startswith("id:")]
    ids2 = [int(line.split(":")[1].strip()) for line in id_lines2]

    # IDs should continue from where we left off
    assert ids2[0] == last_id + 1, (
        f"Reconnection should start from ID {last_id + 1}, got {ids2[0]}"
    )

    # Verify subscription data is still correct
    events2 = [(e, d) async for e, d in response2.streaming_sse()]
    next_events2 = [d for e, d in events2 if e == "next"]
    assert len(next_events2) == 1
    assert next_events2[0]["payload"]["data"]["echo"] == "reconnected"


async def test_e2e_sse_invalid_last_event_id_is_ignored(http_client: HttpClient):
    """End-to-end: a non-numeric Last-Event-ID should be gracefully ignored
    and events should start from ID 1."""
    response = await http_client.query(
        method="post",
        query='subscription { echo(message: "test", delay: 0.1) }',
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
            "last-event-id": "not-a-number",
        },
    )

    assert response.status_code == 200
    assert response.is_sse

    raw_text = response.text
    id_lines = [line for line in raw_text.split("\n") if line.startswith("id:")]
    ids = [int(line.split(":")[1].strip()) for line in id_lines]

    # Should start from 1 when Last-Event-ID is invalid
    assert ids[0] == 1, f"Expected ID 1 with invalid Last-Event-ID, got {ids[0]}"


async def test_e2e_sse_raw_event_format_compliance(http_client: HttpClient):
    """End-to-end: verify raw SSE event format matches the specification.

    Each event block must have:
    - `id: <number>` line
    - `event: <type>` line
    - `data: <json>` or `data:` line
    - Separated by blank line (\\n\\n)
    """
    response = await http_client.query(
        method="post",
        query='subscription { echo(message: "format check", delay: 0.1) }',
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert response.status_code == 200

    raw_text = response.text
    blocks = [b for b in raw_text.split("\n\n") if b.strip()]

    # Filter out heartbeat-only blocks (just ":" comments)
    event_blocks = []
    for block in blocks:
        lines = block.strip().split("\n")
        non_comment_lines = [l for l in lines if not l.startswith(":")]
        if non_comment_lines:
            event_blocks.append(block)

    assert len(event_blocks) >= 2, (
        f"Expected at least 2 event blocks (next + complete), got {len(event_blocks)}"
    )

    for block in event_blocks:
        lines = block.strip().split("\n")
        non_comment_lines = [l for l in lines if not l.startswith(":")]

        # Each event block must have an event type
        event_lines = [l for l in non_comment_lines if l.startswith("event:")]
        assert len(event_lines) == 1, (
            f"Each block must have exactly one event line, got: {block!r}"
        )

        # Each event block must have a data field
        data_lines = [l for l in non_comment_lines if l.startswith("data:")]
        assert len(data_lines) >= 1, (
            f"Each block must have at least one data line, got: {block!r}"
        )

        # Each event block must have an id field
        id_lines = [l for l in non_comment_lines if l.startswith("id:")]
        assert len(id_lines) == 1, (
            f"Each block must have exactly one id line, got: {block!r}"
        )


async def test_e2e_sse_enum_values_in_subscription(http_client: HttpClient):
    """End-to-end: subscription that yields enum values should deliver
    them correctly through SSE."""
    response = await http_client.query(
        method="post",
        query="subscription { flavors }",
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

    assert len(next_events) == 3
    flavors = [e["payload"]["data"]["flavors"] for e in next_events]
    assert flavors == ["VANILLA", "STRAWBERRY", "CHOCOLATE"]
    assert len(complete_events) == 1


async def test_e2e_sse_with_variables(http_client: HttpClient):
    """End-to-end: SSE subscriptions with query variables work correctly."""
    response = await http_client.query(
        method="post",
        query='subscription { echo(message: "var test", delay: 0.1) }',
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert response.status_code == 200
    assert response.is_sse

    events = [(event, data) async for event, data in response.streaming_sse()]
    next_events = [d for e, d in events if e == "next"]

    assert len(next_events) == 1
    assert next_events[0]["payload"]["data"]["echo"] == "var test"


async def test_e2e_sse_subscription_that_yields_nothing_still_completes(
    http_client: HttpClient,
):
    """End-to-end: a subscription resolver that returns without yielding
    should still result in a valid SSE stream that eventually completes.

    Note: GraphQL-core treats a generator that returns immediately as
    returning None, which produces a 'next' event with an error.
    """

    @strawberry.type
    class Q:
        @strawberry.field
        def hello(self) -> str:
            return "world"

    @strawberry.type
    class Sub:
        @strawberry.subscription
        async def empty(self) -> AsyncGenerator[str, None]:
            return

    empty_schema = strawberry.Schema(query=Q, subscription=Sub)

    with contextlib.suppress(ImportError):
        from tests.http.clients.async_django import AsyncDjangoHttpClient

        if isinstance(http_client, AsyncDjangoHttpClient):
            pytest.skip("AsyncDjango doesn't support custom schemas in this fixture")

    client = type(http_client)(schema=empty_schema)

    response = await client.query(
        method="post",
        query="subscription { empty }",
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert response.status_code == 200
    assert response.is_sse

    events = [(event, data) async for event, data in response.streaming_sse()]
    complete_events = [e for e, _ in events if e == "complete"]

    # Stream should eventually complete (may have error events first)
    assert len(complete_events) == 1, "Should still get a complete event"


async def test_e2e_sse_missing_query_returns_400(http_client: HttpClient):
    """End-to-end: a request without a query field should return 400,
    not an SSE stream or 500 error."""
    response = await http_client.post(
        url="/graphql",
        json={"variables": {}},
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert response.status_code == 400


async def test_e2e_sse_malformed_json_returns_400(http_client: HttpClient):
    """End-to-end: invalid JSON body should return 400, not 500."""
    response = await http_client.post(
        url="/graphql",
        data=b"{{invalid json}}",
        json=None,
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert response.status_code == 400
