"""Tests for SSE authentication via on_sse_connect hook."""

import strawberry
from strawberry.exceptions import ConnectionRejectionError
from tests.http.clients.asgi import AsgiHttpClient
from tests.views.schema import Query, Subscription


async def test_sse_connect_rejection_returns_forbidden_error_event():
    """When on_sse_connect raises ConnectionRejectionError, the server should
    return a 200 response with an error event containing 'Forbidden'."""
    schema = strawberry.Schema(query=Query, subscription=Subscription)
    http_client = AsgiHttpClient(schema=schema)
    view = http_client.client.app
    original = view.on_sse_connect

    async def reject(context):
        raise ConnectionRejectionError

    view.on_sse_connect = reject  # type: ignore
    try:
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
        error_events = [d for e, d in events if e == "error"]

        assert len(error_events) == 1
        assert error_events[0] == [{"message": "Forbidden", "code": "FORBIDDEN"}]
    finally:
        view.on_sse_connect = original


async def test_sse_connect_acceptance_proceeds_normally():
    """When on_sse_connect returns UNSET (or doesn't reject), the connection
    should be accepted and the subscription should proceed normally."""
    schema = strawberry.Schema(query=Query, subscription=Subscription)
    http_client = AsgiHttpClient(schema=schema)

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


async def test_sse_connect_with_custom_rejection_payload():
    """When on_sse_connect raises ConnectionRejectionError with a custom payload,
    the error event should contain the custom payload."""
    schema = strawberry.Schema(query=Query, subscription=Subscription)
    http_client = AsgiHttpClient(schema=schema)
    view = http_client.client.app
    original = view.on_sse_connect

    async def custom_reject(context):
        raise ConnectionRejectionError(
            {"message": "Custom rejection", "code": "CUSTOM_ERROR"}
        )

    view.on_sse_connect = custom_reject  # type: ignore
    try:
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
        error_events = [d for e, d in events if e == "error"]

        assert len(error_events) == 1
        assert error_events[0] == [
            {"message": "Custom rejection", "code": "CUSTOM_ERROR"}
        ]
    finally:
        view.on_sse_connect = original


async def test_sse_connect_can_modify_context():
    """When on_sse_connect modifies the context, the modification should
    be visible to the subscription resolver via info.context."""
    schema = strawberry.Schema(query=Query, subscription=Subscription)
    http_client = AsgiHttpClient(schema=schema)
    view = http_client.client.app
    original = view.on_sse_connect

    async def modify_context(context):
        context["modified"] = True

    view.on_sse_connect = modify_context  # type: ignore
    try:
        response = await http_client.query(
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
