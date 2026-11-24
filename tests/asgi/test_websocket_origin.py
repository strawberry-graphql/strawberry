from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

import pytest

import strawberry
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL

if TYPE_CHECKING:
    from starlette.websockets import WebSocket

    from strawberry.asgi import GraphQL


@strawberry.type
class Query:
    hello: str = "world"


schema = strawberry.Schema(Query)


def make_recording_app(**kwargs: Any) -> tuple[GraphQL, list[str]]:
    from strawberry.asgi import GraphQL

    calls: list[str] = []

    class RecordingGraphQL(GraphQL):
        async def get_root_value(self, request: Any) -> None:
            calls.append("get_root_value")

        async def get_context(self, request: Any, response: Any) -> dict[str, Any]:
            calls.append("get_context")
            return {"request": request}

        async def on_ws_connect(self, context: dict[str, Any]) -> Any:
            calls.append("on_ws_connect")
            return await super().on_ws_connect(context)

    return RecordingGraphQL(schema, **kwargs), calls


def connect(app: GraphQL, origin: str) -> None:
    from starlette.testclient import TestClient

    client = TestClient(app)
    with client.websocket_connect(
        "/",
        [GRAPHQL_TRANSPORT_WS_PROTOCOL],
        headers={"host": "api.example.com", "origin": origin},
    ) as ws:
        ws.send_json({"type": "connection_init"})
        assert ws.receive_json() == {"type": "connection_ack"}


def test_rejects_before_calling_application_hooks():
    from starlette.websockets import WebSocketDisconnect

    app, calls = make_recording_app()

    with pytest.raises(WebSocketDisconnect) as exc_info:
        connect(app, origin="https://evil.example")

    assert exc_info.value.code == 1008
    assert calls == []


def test_calls_application_hooks_for_allowed_origins():
    app, calls = make_recording_app(allowed_origins=["https://app.example.com"])

    connect(app, origin="https://app.example.com")

    assert calls == ["get_root_value", "get_context", "on_ws_connect"]


def test_is_websocket_origin_allowed_can_be_overridden():
    from starlette.websockets import WebSocketDisconnect

    from strawberry.asgi import GraphQL

    class SubdomainGraphQL(GraphQL):
        def is_websocket_origin_allowed(self, request: WebSocket, origin: str) -> bool:
            host = urlsplit(origin).hostname or ""
            return host == "example.com" or host.endswith(".example.com")

    app = SubdomainGraphQL(schema)

    connect(app, origin="https://app.example.com")

    with pytest.raises(WebSocketDisconnect):
        connect(app, origin="https://example.com.evil.example")


def test_invalid_allowed_origins_fail_at_construction():
    from strawberry.asgi import GraphQL

    with pytest.raises(ValueError, match=r"Invalid origin 'app\.example\.com'"):
        GraphQL(schema, allowed_origins=["app.example.com"])
