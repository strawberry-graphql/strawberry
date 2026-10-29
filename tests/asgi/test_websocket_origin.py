from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocket, WebSocketDisconnect

import strawberry
from strawberry.asgi import GraphQL
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL


@strawberry.type
class Query:
    hello: str = "world"


schema = strawberry.Schema(Query)


class RecordingGraphQL(GraphQL):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.calls: list[str] = []

    async def get_root_value(self, request: Any) -> None:
        self.calls.append("get_root_value")

    async def get_context(self, request: Any, response: Any) -> dict[str, Any]:
        self.calls.append("get_context")
        return {"request": request}

    async def on_ws_connect(self, context: dict[str, Any]) -> Any:
        self.calls.append("on_ws_connect")
        return await super().on_ws_connect(context)


class SubdomainGraphQL(GraphQL):
    def is_websocket_origin_allowed(self, request: WebSocket, origin: str) -> bool:
        host = urlsplit(origin).hostname or ""
        return host == "example.com" or host.endswith(".example.com")


def connect(app: GraphQL, origin: str) -> None:
    client = TestClient(app)
    with client.websocket_connect(
        "/",
        [GRAPHQL_TRANSPORT_WS_PROTOCOL],
        headers={"host": "api.example.com", "origin": origin},
    ) as ws:
        ws.send_json({"type": "connection_init"})
        assert ws.receive_json() == {"type": "connection_ack"}


def test_rejects_before_calling_application_hooks():
    app = RecordingGraphQL(schema)

    with pytest.raises(WebSocketDisconnect) as exc_info:
        connect(app, origin="https://evil.example")

    assert exc_info.value.code == 1008
    assert app.calls == []


def test_calls_application_hooks_for_allowed_origins():
    app = RecordingGraphQL(schema, allowed_origins=["https://app.example.com"])

    connect(app, origin="https://app.example.com")

    assert app.calls == ["get_root_value", "get_context", "on_ws_connect"]


def test_is_websocket_origin_allowed_can_be_overridden():
    app = SubdomainGraphQL(schema)

    connect(app, origin="https://app.example.com")

    with pytest.raises(WebSocketDisconnect):
        connect(app, origin="https://example.com.evil.example")


def test_invalid_allowed_origins_fail_at_construction():
    with pytest.raises(ValueError, match=r"Invalid origin 'app\.example\.com'"):
        GraphQL(schema, allowed_origins=["app.example.com"])
