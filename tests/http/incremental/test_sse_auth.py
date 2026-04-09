"""Tests for SSE authentication via on_sse_connect hook."""

import contextlib

import pytest

import strawberry
from strawberry.exceptions import ConnectionRejectionError
from tests.http.clients.base import HttpClient
from tests.views.schema import Query, Subscription


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
        schema=strawberry.Schema(query=Query, subscription=Subscription)
    )


@pytest.fixture
def patchable_http_client(http_client_class: type[HttpClient]) -> HttpClient | None:
    """Provide HTTP clients that expose their view for patching."""
    with contextlib.suppress(ImportError):
        from tests.http.clients.asgi import AsgiHttpClient

        if http_client_class is not AsgiHttpClient:
            pytest.skip("Only AsgiHttpClient exposes view for patching")

        return http_client_class(
            schema=strawberry.Schema(query=Query, subscription=Subscription)
        )

    pytest.skip("AsgiHttpClient not available")


async def test_sse_connect_rejection_returns_forbidden_error_event(
    patchable_http_client: HttpClient,
):
    """When on_sse_connect raises ConnectionRejectionError, the server should
    return a 200 response with an error event containing 'Forbidden'."""
    view = patchable_http_client.client.app
    original = view.on_sse_connect

    async def reject(context):
        raise ConnectionRejectionError

    view.on_sse_connect = reject  # type: ignore
    try:
        response = await patchable_http_client.query(
            method="post",
            query='subscription { echo(message: "test", delay: 0.2) }',
            headers={
                "accept": "text/event-stream",
                "content-type": "application/json",
            },
        )

        assert response.status_code == 200
        assert response.is_sse

        events = [(e, d) async for e, d in response.streaming_sse()]
        error_events = [d for e, d in events if e == "error"]

        assert len(error_events) == 1
        assert error_events[0] == [{"message": "Forbidden", "code": "FORBIDDEN"}]
    finally:
        view.on_sse_connect = original


async def test_sse_connect_acceptance_proceeds_normally(http_client: HttpClient):
    """When on_sse_connect returns UNSET (or doesn't reject), the connection
    should be accepted and the subscription should proceed normally."""
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

    events = [(e, d) async for e, d in response.streaming_sse()]
    next_events = [d for e, d in events if e == "next"]

    assert len(next_events) == 1
    assert next_events[0]["payload"]["data"]["echo"] == "test"


async def test_sse_connect_with_custom_rejection_payload(
    patchable_http_client: HttpClient,
):
    """When on_sse_connect raises ConnectionRejectionError with a custom payload,
    the error event should contain the custom payload."""
    view = patchable_http_client.client.app
    original = view.on_sse_connect

    async def custom_reject(context):
        raise ConnectionRejectionError(
            {"message": "Custom rejection", "code": "CUSTOM_ERROR"}
        )

    view.on_sse_connect = custom_reject  # type: ignore
    try:
        response = await patchable_http_client.query(
            method="post",
            query='subscription { echo(message: "test", delay: 0.2) }',
            headers={
                "accept": "text/event-stream",
                "content-type": "application/json",
            },
        )

        assert response.status_code == 200
        assert response.is_sse

        events = [(e, d) async for e, d in response.streaming_sse()]
        error_events = [d for e, d in events if e == "error"]

        assert len(error_events) == 1
        assert error_events[0] == [
            {"message": "Custom rejection", "code": "CUSTOM_ERROR"}
        ]
    finally:
        view.on_sse_connect = original


async def test_sse_connect_can_modify_context(
    patchable_http_client: HttpClient,
):
    """When on_sse_connect modifies the context, the modification should
    be visible to the subscription resolver via info.context."""
    view = patchable_http_client.client.app
    original = view.on_sse_connect

    async def modify_context(context):
        context["modified"] = True

    view.on_sse_connect = modify_context  # type: ignore
    try:
        response = await patchable_http_client.query(
            method="post",
            query="subscription { contextValues }",
            headers={
                "accept": "text/event-stream",
                "content-type": "application/json",
            },
        )

        assert response.status_code == 200
        assert response.is_sse

        events = [(e, d) async for e, d in response.streaming_sse()]
        next_events = [d for e, d in events if e == "next"]

        assert len(next_events) == 1
        assert next_events[0]["payload"]["data"]["contextValues"] is True
    finally:
        view.on_sse_connect = original
