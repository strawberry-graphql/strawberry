import contextlib
from collections.abc import AsyncGenerator
from typing import Any

import pytest

import strawberry
from strawberry.extensions import SchemaExtension
from strawberry.subscriptions import (
    GRAPHQL_SSE_PROTOCOL,
    GRAPHQL_TRANSPORT_WS_PROTOCOL,
    GRAPHQL_WS_PROTOCOL,
)
from tests.http.clients.base import HttpClient
from tests.views.schema import schema


class FederationExtension(SchemaExtension):
    """Extension that adds federation tracing info to results."""

    async def get_results(self) -> dict[str, Any]:
        return {"federation": {"trace": "extension_active"}}


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


async def test_sse_subscription_with_federation_schema(
    incremental_http_client_class: type[HttpClient],
):
    """SSE subscriptions should work with Apollo Federation schemas.

    This verifies that federation directives and entity resolution don't
    interfere with SSE subscription handling.
    """
    from strawberry.federation import Schema as FederationSchema

    @strawberry.federation.type(keys=["upc"])
    class Product:
        upc: str
        name: str

        @classmethod
        def resolve_reference(cls, upc: str) -> "Product":
            return Product(upc=upc, name=f"Product {upc}")

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def product(self, upc: str) -> Product | None:
            return Product(upc=upc, name=f"Product {upc}")

    @strawberry.type
    class Subscription:
        @strawberry.subscription
        async def count(self, target: int = 3) -> AsyncGenerator[int, None]:
            for i in range(target):
                yield i

    fed_schema = FederationSchema(query=Query, subscription=Subscription)

    http_client = incremental_http_client_class(
        schema=fed_schema,
        subscription_protocols=(
            GRAPHQL_TRANSPORT_WS_PROTOCOL,
            GRAPHQL_WS_PROTOCOL,
            GRAPHQL_SSE_PROTOCOL,
        ),
    )

    response = await http_client.query(
        method="post",
        query="subscription { count(target: 3) }",
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
    assert [next_events[0], next_events[1], next_events[2]] == [
        {"payload": {"data": {"count": 0}}},
        {"payload": {"data": {"count": 1}}},
        {"payload": {"data": {"count": 2}}},
    ]
    assert len(complete_events) == 1


async def test_sse_subscription_with_federation_and_entities(
    incremental_http_client_class: type[HttpClient],
):
    """SSE subscriptions work alongside federation entity resolution.

    This test verifies that subscriptions and entity resolution coexist
    without conflict when using federation schema.
    """
    from strawberry.federation import Schema as FederationSchema

    @strawberry.federation.type(keys=["id"])
    class User:
        id: strawberry.ID
        name: str

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def user(self, id: strawberry.ID) -> User | None:
            return User(id=id, name=f"User {id}")

    @strawberry.type
    class Subscription:
        @strawberry.subscription
        async def notify_user(
            self, user_id: strawberry.ID
        ) -> AsyncGenerator[str, None]:
            yield f"User {user_id} updated"

    fed_schema = FederationSchema(query=Query, subscription=Subscription)

    http_client = incremental_http_client_class(
        schema=fed_schema,
        subscription_protocols=(
            GRAPHQL_TRANSPORT_WS_PROTOCOL,
            GRAPHQL_WS_PROTOCOL,
            GRAPHQL_SSE_PROTOCOL,
        ),
    )

    response = await http_client.query(
        method="post",
        query='subscription { notifyUser(userId: "123") }',
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
    assert next_events[0]["payload"]["data"]["notifyUser"] == "User 123 updated"
    assert len(complete_events) == 1


async def test_sse_subscription_with_extension(
    incremental_http_client_class: type[HttpClient],
):
    """SSE subscriptions should include extension results in each event.

    Extensions are called once per subscription start (lifecycle hooks) and
    once per yielded value (get_results). This test verifies extension
    results appear in SSE next events.
    """
    from strawberry.extensions import SchemaExtension

    class TestExtension(SchemaExtension):
        async def get_results(self) -> dict[str, Any]:
            return {"test": {"extension_ran": True}}

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

    @strawberry.type
    class Subscription:
        @strawberry.subscription
        async def count(self, target: int = 2) -> AsyncGenerator[int, None]:
            for i in range(target):
                yield i

    test_schema = strawberry.Schema(
        query=Query,
        subscription=Subscription,
        extensions=[TestExtension],
    )

    http_client = incremental_http_client_class(
        schema=test_schema,
        subscription_protocols=(
            GRAPHQL_TRANSPORT_WS_PROTOCOL,
            GRAPHQL_WS_PROTOCOL,
            GRAPHQL_SSE_PROTOCOL,
        ),
    )

    response = await http_client.query(
        method="post",
        query="subscription { count(target: 2) }",
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert response.status_code == 200
    assert response.is_sse

    events = [(event, data) async for event, data in response.streaming_sse()]
    next_events = [d for e, d in events if e == "next"]

    assert len(next_events) == 2
    for next_event in next_events:
        assert "extensions" in next_event["payload"], (
            f"Extension results missing from event: {next_event}"
        )
        assert "test" in next_event["payload"]["extensions"], (
            f"Extension results missing from event: {next_event}"
        )
        assert next_event["payload"]["extensions"]["test"]["extension_ran"] is True


async def test_sse_subscription_reconnects_from_last_event_id(
    incremental_http_client_class: type[HttpClient],
):
    """When a client reconnects with Last-Event-ID, server starts from that point.

    This verifies the server correctly parses Last-Event-ID and continues
    event numbering, allowing clients to resume after connection drops.
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


async def test_sse_subscription_full_reconnection_flow(
    incremental_http_client_class: type[HttpClient],
):
    """Simulates a full reconnection flow where client resumes from last event.

    Steps:
    1. Start subscription, receive events with IDs 1, 2
    2. Simulate disconnect and reconnect with Last-Event-ID: 2
    3. Server should resume from ID 3
    """
    from strawberry.extensions import SchemaExtension

    call_count = 0

    class CountingExtension(SchemaExtension):
        async def get_results(self) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            return {"callNumber": call_count}

    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

    @strawberry.type
    class Subscription:
        @strawberry.subscription
        async def count(self, target: int = 3) -> AsyncGenerator[int, None]:
            for i in range(target):
                yield i

    test_schema = strawberry.Schema(
        query=Query,
        subscription=Subscription,
        extensions=[CountingExtension],
    )

    http_client = incremental_http_client_class(
        schema=test_schema,
        subscription_protocols=(
            GRAPHQL_TRANSPORT_WS_PROTOCOL,
            GRAPHQL_WS_PROTOCOL,
            GRAPHQL_SSE_PROTOCOL,
        ),
    )

    response1 = await http_client.query(
        method="post",
        query="subscription { count(target: 2) }",
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert response1.status_code == 200
    raw_text1 = response1.text
    id_lines1 = [
        int(line.split(":")[1].strip())
        for line in raw_text1.split("\n")
        if line.startswith("id:")
    ]
    assert id_lines1 == [1, 2, 3], (
        f"First subscription IDs should be 1, 2, 3, got {id_lines1}"
    )

    response2 = await http_client.query(
        method="post",
        query="subscription { count(target: 2) }",
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
            "last-event-id": "3",
        },
    )

    assert response2.status_code == 200
    raw_text2 = response2.text
    id_lines2 = [
        int(line.split(":")[1].strip())
        for line in raw_text2.split("\n")
        if line.startswith("id:")
    ]
    assert id_lines2 == [4, 5, 6], (
        f"Reconnection IDs should be 4, 5, 6, got {id_lines2}"
    )
