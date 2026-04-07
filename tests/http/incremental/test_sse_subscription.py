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
            pytest.skip(
                reason="FlaskHttpClient doesn't support SSE subscriptions"
            )

        if http_client_class is AsyncFlaskHttpClient:
            pytest.xfail(
                reason="AsyncFlaskHttpClient doesn't support SSE subscriptions"
            )

    with contextlib.suppress(ImportError):
        from tests.http.clients.chalice import ChaliceHttpClient

        if http_client_class is ChaliceHttpClient:
            pytest.skip(
                reason="ChaliceHttpClient doesn't support SSE subscriptions"
            )

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
    http_client_class: type[HttpClient],
):
    http_client = http_client_class(
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
