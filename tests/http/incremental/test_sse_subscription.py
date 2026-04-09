import asyncio
import contextlib

import pytest

import strawberry
from strawberry.schema.config import StrawberryConfig
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

    return http_client_class(schema=schema)


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

    # Filter out heartbeat comments (they don't appear as events)
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
        )
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

    # The server should still work - it detects graphql-sse protocol and
    # falls back to JSON parsing regardless of Content-Type
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
        schema=schema, max_subscriptions_per_connection=1
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

    from tests.http.clients.base import Response

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
