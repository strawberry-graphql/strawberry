import asyncio
import contextlib
import json
from collections.abc import AsyncIterable
from typing import Literal

import pytest

import strawberry
from strawberry.http.base import BaseView
from strawberry.http.streaming import SSETransport
from strawberry.schema.config import StrawberryConfig
from strawberry.subscriptions import (
    GRAPHQL_SSE_PROTOCOL,
    GRAPHQL_TRANSPORT_WS_PROTOCOL,
    GRAPHQL_WS_PROTOCOL,
)
from strawberry.types import ExecutionResult
from tests.conftest import skip_if_gql_32
from tests.http.clients.base import HttpClient
from tests.views.schema import Mutation, MyExtension, Query, Subscription, schema

SSE_SUBSCRIPTION_PROTOCOLS = (
    GRAPHQL_TRANSPORT_WS_PROTOCOL,
    GRAPHQL_WS_PROTOCOL,
    GRAPHQL_SSE_PROTOCOL,
)


def create_sse_http_client(
    http_client_class: type[HttpClient], graphql_schema=schema
) -> HttpClient:
    with contextlib.suppress(ImportError):
        import django

        if django.VERSION < (4, 2):
            pytest.skip(reason="Django < 4.2 doesn't async streaming responses")

        from tests.http.clients.django import DjangoHttpClient

        if http_client_class is DjangoHttpClient:
            pytest.skip(reason="(sync) DjangoHttpClient doesn't support SSE streams")

    with contextlib.suppress(ImportError):
        from tests.http.clients.channels import SyncChannelsHttpClient

        if http_client_class is SyncChannelsHttpClient:
            pytest.skip(reason="SyncChannelsHttpClient doesn't support SSE streams")

    with contextlib.suppress(ImportError):
        from tests.http.clients.async_flask import AsyncFlaskHttpClient
        from tests.http.clients.flask import FlaskHttpClient

        if http_client_class is FlaskHttpClient:
            pytest.skip(reason="FlaskHttpClient doesn't support SSE streams")

        if http_client_class is AsyncFlaskHttpClient:
            pytest.xfail(reason="AsyncFlaskHttpClient doesn't support SSE streams")

    with contextlib.suppress(ImportError):
        from tests.http.clients.chalice import ChaliceHttpClient

        if http_client_class is ChaliceHttpClient:
            pytest.skip(reason="ChaliceHttpClient doesn't support SSE streams")

    return http_client_class(
        schema=graphql_schema,
        subscription_protocols=SSE_SUBSCRIPTION_PROTOCOLS,
    )


@pytest.fixture
def http_client(http_client_class: type[HttpClient]) -> HttpClient:
    return create_sse_http_client(http_client_class)


def parse_sse_events(body: str) -> list[tuple[str, object | None]]:
    events = []

    for block in body.replace("\r\n", "\n").split("\n\n"):
        if not block:
            continue

        event = "message"
        data = []
        has_fields = False

        for line in block.splitlines():
            if line.startswith("event:"):
                event = line.removeprefix("event:").strip()
                has_fields = True
            elif line.startswith("data:"):
                data.append(line.removeprefix("data:").lstrip())
                has_fields = True

        if not has_fields:
            continue

        raw_data = "\n".join(data)

        events.append((event, json.loads(raw_data) if raw_data else ""))

    return events


async def get_response_text(response) -> str:
    if isinstance(response.data, AsyncIterable):
        chunks = [chunk async for chunk in response.data]

        return b"".join(chunks).decode()

    return response.text


def assert_sse_response(response) -> None:
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")


def assert_single_sse_error(
    events: list[tuple[str, object | None]], expected_message: str
) -> None:
    assert len(events) == 2
    event, payload = events[0]

    assert event == "next"
    assert isinstance(payload, dict)
    assert payload["data"] is None
    assert expected_message in payload["errors"][0]["message"]
    assert payload["extensions"] == {"example": "example"}
    assert events[1] == ("complete", "")


async def test_sse_requires_enabled_protocol(http_client_class: type[HttpClient]):
    # A client without graphql-sse in its protocols must not serve SSE.
    http_client = http_client_class(schema)

    response = await http_client.query(
        query='subscription { echo(message: "Hello world") }',
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert not response.headers["content-type"].startswith("text/event-stream")
    assert parse_sse_events(response.text) == []


@pytest.mark.parametrize(
    "accept_header",
    [
        pytest.param("text/event-stream; charset=utf-8", id="with-params"),
        pytest.param("application/json, text/event-stream", id="multiple-values"),
        pytest.param("TEXT/EVENT-STREAM", id="case-insensitive"),
    ],
)
async def test_sse_accept_header_parsing(http_client: HttpClient, accept_header: str):
    response = await http_client.query(
        query="{ hello }",
        headers={
            "accept": accept_header,
            "content-type": "application/json",
        },
    )

    assert_sse_response(response)
    assert parse_sse_events(await get_response_text(response)) == [
        (
            "next",
            {
                "data": {"hello": "Hello world"},
                "extensions": {"example": "example"},
            },
        ),
        ("complete", ""),
    ]


@pytest.mark.parametrize("method", ["get", "post"])
async def test_sse_subscription(
    http_client: HttpClient, method: Literal["get", "post"]
):
    response = await http_client.query(
        method=method,
        query='subscription { echo(message: "Hello world", delay: 0.2) }',
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["cache-control"] == "no-cache"
    assert response.headers["x-accel-buffering"] == "no"
    assert parse_sse_events(await get_response_text(response)) == [
        (
            "next",
            {
                "data": {"echo": "Hello world"},
                "extensions": {"example": "example"},
            },
        ),
        ("complete", ""),
    ]


async def test_sse_subscription_use_the_views_decode_json_method(
    http_client: HttpClient, mocker
):
    spy = mocker.spy(BaseView, "decode_json")

    response = await http_client.query(
        query='subscription { echo(message: "Hello world", delay: 0.2) }',
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert response.status_code == 200
    assert parse_sse_events(await get_response_text(response)) == [
        (
            "next",
            {
                "data": {"echo": "Hello world"},
                "extensions": {"example": "example"},
            },
        ),
        ("complete", ""),
    ]

    assert spy.call_count == 1


async def test_sse_supports_bytes_encoded_json(http_client: HttpClient, mocker):
    def patched_encode_json(self, data: object) -> bytes:
        return json.dumps(data).encode()

    mocker.patch("strawberry.http.base.BaseView.encode_json", patched_encode_json)

    response = await http_client.query(
        query="{ hello }",
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert_sse_response(response)
    assert parse_sse_events(await get_response_text(response)) == [
        (
            "next",
            {
                "data": {"hello": "Hello world"},
                "extensions": {"example": "example"},
            },
        ),
        ("complete", ""),
    ]


async def test_sse_subscription_sends_heartbeat_while_idle():
    asgi = pytest.importorskip("tests.http.clients.asgi")
    view = asgi.GraphQLView(schema)
    transport = SSETransport(heartbeat_interval=0.01)

    async def result():
        await asyncio.sleep(0.03)
        yield ExecutionResult(
            data={"echo": "Hello world"},
            errors=None,
            extensions={"example": "example"},
        )

    stream = view._stream_result(None, result(), transport)
    chunks = [chunk async for chunk in stream()]
    body = "".join(chunks)

    assert ": ping\r\n\r\n" in body
    assert parse_sse_events(body) == [
        (
            "next",
            {
                "data": {"echo": "Hello world"},
                "extensions": {"example": "example"},
            },
        ),
        ("complete", ""),
    ]


async def test_sse_does_not_emit_event_ids(http_client: HttpClient):
    """Strawberry follows graphql-sse and never emits an SSE ``id:`` line."""
    response = await http_client.query(
        query="{ hello }",
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert_sse_response(response)
    body = await get_response_text(response)
    assert "id: " not in body


def test_sse_rejects_multiline_encoded_data():
    """SSE data must be a single line; a multi-line encoder output is rejected."""
    transport = SSETransport()

    with pytest.raises(ValueError, match="must not contain newlines"):
        transport.encode_next({"data": None}, lambda _: '{\n  "data": null\n}')


def test_websocket_subprotocols_excludes_sse():
    asgi = pytest.importorskip("tests.http.clients.asgi")
    view = asgi.GraphQLView(
        schema,
        subscription_protocols=[
            GRAPHQL_TRANSPORT_WS_PROTOCOL,
            GRAPHQL_WS_PROTOCOL,
            GRAPHQL_SSE_PROTOCOL,
        ],
    )

    # graphql-sse enables the SSE transport but must not be advertised as a
    # WebSocket subprotocol during the handshake.
    assert view.websocket_subprotocols == [
        GRAPHQL_TRANSPORT_WS_PROTOCOL,
        GRAPHQL_WS_PROTOCOL,
    ]
    assert (
        view._get_stream_transport_from_headers({"accept": "text/event-stream"})
        is not None
    )


async def test_sse_query(http_client: HttpClient):
    response = await http_client.query(
        query="{ hello }",
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert parse_sse_events(await get_response_text(response)) == [
        (
            "next",
            {
                "data": {"hello": "Hello world"},
                "extensions": {"example": "example"},
            },
        ),
        ("complete", ""),
    ]


@pytest.mark.parametrize(
    ("method", "expected_payload"),
    [
        pytest.param(
            "post",
            {"data": {"hello": "strawberry"}, "extensions": {"example": "example"}},
            id="post",
        ),
        pytest.param(
            "get",
            {
                "data": None,
                "errors": [{"message": "mutations are not allowed"}],
                "extensions": {"example": "example"},
            },
            id="get",
        ),
    ],
)
async def test_sse_mutation(
    http_client: HttpClient,
    method: Literal["get", "post"],
    expected_payload: object,
):
    response = await http_client.query(
        method=method,
        query="mutation { hello }",
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert_sse_response(response)
    assert parse_sse_events(await get_response_text(response)) == [
        ("next", expected_payload),
        ("complete", ""),
    ]


async def test_sse_uses_http_context_for_authentication(http_client: HttpClient):
    response = await http_client.query(
        query='{ valueFromContext(key: "authorization") }',
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
            "Authorization": "Bearer strawberry",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert parse_sse_events(await get_response_text(response)) == [
        (
            "next",
            {
                "data": {"valueFromContext": "Bearer strawberry"},
                "extensions": {"example": "example"},
            },
        ),
        ("complete", ""),
    ]


async def test_sse_query_permission_errors(http_client: HttpClient):
    response = await http_client.query(
        query="{ hello, alwaysFail }",
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert_sse_response(response)

    events = parse_sse_events(await get_response_text(response))
    assert len(events) == 2

    event, payload = events[0]
    assert event == "next"
    assert isinstance(payload, dict)
    assert payload["data"] == {"hello": "Hello world", "alwaysFail": None}
    assert payload["errors"][0]["message"] == "You are not authorized"
    assert payload["errors"][0]["path"] == ["alwaysFail"]
    assert payload["extensions"] == {"example": "example"}
    assert events[1] == ("complete", "")


async def test_sse_subscription_resolver_exception_completes_stream(
    http_client: HttpClient,
):
    """A subscription resolver that raises is delivered as a ``next`` event with
    ``errors`` and the stream is still terminated with a ``complete`` event,
    rather than aborting the connection."""
    response = await http_client.query(
        query='subscription { exception(message: "boom") }',
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert_sse_response(response)

    events = parse_sse_events(await get_response_text(response))
    assert len(events) == 2

    event, payload = events[0]
    assert event == "next"
    assert isinstance(payload, dict)
    assert payload["data"] is None
    assert payload["errors"][0]["message"] == "boom"
    assert events[1] == ("complete", "")


async def test_sse_subscription_error_event_completes_stream(http_client: HttpClient):
    """A subscription that yields a ``GraphQLError`` reports it through a ``next``
    event followed by ``complete``."""
    response = await http_client.query(
        query='subscription { error(message: "graceful") }',
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert_sse_response(response)

    events = parse_sse_events(await get_response_text(response))
    assert len(events) == 2

    event, payload = events[0]
    assert event == "next"
    assert isinstance(payload, dict)
    assert payload["data"] is None
    assert payload["errors"][0]["message"] == "graceful"
    assert events[1] == ("complete", "")


async def test_sse_subscription_mid_stream_error_keeps_streaming(
    http_client: HttpClient,
):
    """An error on a single result does not abort the stream: earlier and later
    results are still delivered, followed by a ``complete`` event."""
    response = await http_client.query(
        query="subscription { flavorsInvalid }",
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert_sse_response(response)

    events = parse_sse_events(await get_response_text(response))
    assert [event for event, _ in events] == ["next", "next", "next", "complete"]

    assert events[0][1] == {
        "data": {"flavorsInvalid": "VANILLA"},
        "extensions": {"example": "example"},
    }

    error_payload = events[1][1]
    assert isinstance(error_payload, dict)
    assert error_payload["data"] is None
    assert "cannot represent value" in error_payload["errors"][0]["message"]

    assert events[2][1] == {
        "data": {"flavorsInvalid": "CHOCOLATE"},
        "extensions": {"example": "example"},
    }
    assert events[3] == ("complete", "")


async def test_sse_missing_query_returns_error_event(http_client: HttpClient):
    response = await http_client.post(
        url="/graphql",
        json={},
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert_sse_response(response)
    assert_single_sse_error(
        parse_sse_events(await get_response_text(response)),
        'Request data is missing a "query" value',
    )


async def test_sse_graphql_parse_error_returns_error_event(http_client: HttpClient):
    response = await http_client.query(
        query="{",
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert_sse_response(response)
    assert_single_sse_error(
        parse_sse_events(await get_response_text(response)),
        "Syntax Error",
    )


@pytest.mark.parametrize(
    ("body", "expected_message"),
    [
        pytest.param(
            {"query": ["array"]},
            "The GraphQL operation's `query` must be a string or null, if provided.",
            id="query",
        ),
        pytest.param(
            {"query": "{ hello }", "variables": ["array"]},
            "The GraphQL operation's `variables` must be an object or null, if provided.",
            id="variables",
        ),
        pytest.param(
            {"query": "{ hello }", "extensions": ["array"]},
            "The GraphQL operation's `extensions` must be an object or null, if provided.",
            id="extensions",
        ),
    ],
)
async def test_sse_rejects_invalid_request_parameters(
    http_client: HttpClient, body: object, expected_message: str
):
    response = await http_client.post(
        url="/graphql",
        json=body,
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("text/plain")
    assert expected_message in response.text


@pytest.mark.parametrize(
    ("data", "content_type", "expected_message"),
    [
        pytest.param(
            b"{ h",
            "application/json",
            "Unable to parse request body as JSON",
            id="malformed-json",
        ),
        pytest.param(
            b"query { hello }",
            "text/plain",
            "Unsupported content type",
            id="unsupported-content-type",
        ),
    ],
)
async def test_sse_rejects_malformed_http_requests(
    http_client: HttpClient,
    data: bytes,
    content_type: str,
    expected_message: str,
):
    response = await http_client.post(
        url="/graphql",
        data=data,
        headers={
            "accept": "text/event-stream",
            "content-type": content_type,
        },
    )

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("text/plain")
    assert expected_message in response.text


async def test_sse_rejects_batching(http_client_class: type[HttpClient]):
    http_client = create_sse_http_client(
        http_client_class,
        strawberry.Schema(
            query=Query,
            mutation=Mutation,
            subscription=Subscription,
            extensions=[MyExtension],
            config=StrawberryConfig(batching_config={"max_operations": 10}),
        ),
    )

    response = await http_client.post(
        url="/graphql",
        json=[
            {"query": "{ hello }"},
            {"query": "{ hello }"},
        ],
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("text/plain")
    assert "Batching is not supported for SSE" in response.text


async def test_sse_large_payload(http_client: HttpClient):
    name = "x" * 65536

    response = await http_client.query(
        query="query ($name: String!) { hello(name: $name) }",
        variables={"name": name},
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert_sse_response(response)
    assert parse_sse_events(await get_response_text(response)) == [
        (
            "next",
            {
                "data": {"hello": f"Hello {name}"},
                "extensions": {"example": "example"},
            },
        ),
        ("complete", ""),
    ]


async def test_sse_streams_data_containing_newlines(http_client: HttpClient):
    """Newlines inside a value are JSON-escaped, so they stream fine and survive
    the round-trip (only a multi-line encoder output is rejected)."""
    name = "line1\nline2\r\nline3"

    response = await http_client.query(
        query="query ($name: String!) { hello(name: $name) }",
        variables={"name": name},
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert_sse_response(response)
    assert parse_sse_events(await get_response_text(response)) == [
        (
            "next",
            {
                "data": {"hello": f"Hello {name}"},
                "extensions": {"example": "example"},
            },
        ),
        ("complete", ""),
    ]


async def test_sse_does_not_replay_from_last_event_id(http_client: HttpClient):
    """Strawberry does nothing with Last-Event-ID itself; it never replays.

    Reading it (to resume) is left to the application via ``get_context``.
    """
    response = await http_client.query(
        query="{ hello }",
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
            "Last-Event-ID": "stale-event-id",
        },
    )

    assert_sse_response(response)
    assert parse_sse_events(await get_response_text(response)) == [
        (
            "next",
            {
                "data": {"hello": "Hello world"},
                "extensions": {"example": "example"},
            },
        ),
        ("complete", ""),
    ]


async def test_sse_federation_query(http_client_class: type[HttpClient]):
    @strawberry.federation.type(keys=["id"])
    class Product:
        id: strawberry.ID
        name: str

    @strawberry.type
    class FederationQuery:
        @strawberry.field
        def product(self) -> Product:
            return Product(id=strawberry.ID("1"), name="Strawberry")

    http_client = create_sse_http_client(
        http_client_class,
        strawberry.federation.Schema(query=FederationQuery),
    )

    response = await http_client.query(
        query="{ _service { sdl } }",
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert_sse_response(response)

    events = parse_sse_events(await get_response_text(response))
    event, payload = events[0]
    assert event == "next"
    assert isinstance(payload, dict)
    assert "type Product" in payload["data"]["_service"]["sdl"]
    assert events[1] == ("complete", "")


async def test_sse_response_uses_streaming_status_and_headers(
    http_client: HttpClient,
):
    response = await http_client.query(
        query='query { returns401 setHeader(name: "Jake") }',
        headers={
            "accept": "text/event-stream",
            "content-type": "application/json",
        },
    )

    assert_sse_response(response)
    assert "x-name" not in response.headers
    assert parse_sse_events(await get_response_text(response)) == [
        (
            "next",
            {
                "data": {
                    "returns401": "hey",
                    "setHeader": "Jake",
                },
                "extensions": {"example": "example"},
            },
        ),
        ("complete", ""),
    ]


@skip_if_gql_32("GraphQL 3.3.0 is required for incremental execution")
async def test_sse_stream_directive(http_client: HttpClient):
    response = await http_client.query(
        method="get",
        query="""
        query Stream {
            streamableField @stream
        }
        """,
        headers={"accept": "text/event-stream"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    events = parse_sse_events(await get_response_text(response))

    assert [event for event, _ in events] == [
        "next",
        "next",
        "next",
        "next",
        "complete",
    ]
    assert events[0] == (
        "next",
        {
            "data": {"streamableField": []},
            "hasNext": True,
            "pending": [{"id": "0", "path": ["streamableField"]}],
            "extensions": {"example": "example"},
        },
    )
    assert events[-2] == (
        "next",
        {
            "hasNext": False,
            "extensions": None,
            "completed": [{"id": "0"}],
        },
    )
    assert events[-1] == ("complete", "")
