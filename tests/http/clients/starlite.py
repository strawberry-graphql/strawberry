from __future__ import annotations

import contextlib
import json
from io import BytesIO
from typing import Any, AsyncGenerator, Dict, List, Optional
from typing_extensions import Literal

from starlite import Request, Starlite
from starlite.exceptions import WebSocketDisconnect
from starlite.testing import TestClient
from starlite.testing.websocket_test_session import WebSocketTestSession
from strawberry.http import GraphQLHTTPResponse
from strawberry.http.ides import GraphQL_IDE
from strawberry.starlite import make_graphql_controller
from strawberry.starlite.controller import GraphQLTransportWSHandler, GraphQLWSHandler
from strawberry.types import ExecutionResult
from tests.views.schema import Query, schema

from ..context import get_context
from .base import (
    JSON,
    DebuggableGraphQLTransportWSMixin,
    DebuggableGraphQLWSMixin,
    HttpClient,
    Message,
    Response,
    ResultOverrideFunction,
    WebSocketClient,
)


def custom_context_dependency() -> str:
    return "Hi!"


async def starlite_get_context(request: Request = None):
    return get_context({"request": request})


async def get_root_value(request: Request = None):
    return Query()


class DebuggableGraphQLTransportWSHandler(
    DebuggableGraphQLTransportWSMixin, GraphQLTransportWSHandler
):
    pass


class DebuggableGraphQLWSHandler(DebuggableGraphQLWSMixin, GraphQLWSHandler):
    pass


class StarliteHttpClient(HttpClient):
    def __init__(
        self,
        graphiql: Optional[bool] = None,
        graphql_ide: Optional[GraphQL_IDE] = "graphiql",
        allow_queries_via_get: bool = True,
        result_override: ResultOverrideFunction = None,
    ):
        self.create_app(
            graphiql=graphiql,
            graphql_ide=graphql_ide,
            allow_queries_via_get=allow_queries_via_get,
            result_override=result_override,
        )

    def create_app(self, result_override: ResultOverrideFunction = None, **kwargs: Any):
        BaseGraphQLController = make_graphql_controller(
            schema=schema,
            path="/graphql",
            context_getter=starlite_get_context,
            root_value_getter=get_root_value,
            **kwargs,
        )

        class GraphQLController(BaseGraphQLController):
            graphql_transport_ws_handler_class = DebuggableGraphQLTransportWSHandler
            graphql_ws_handler_class = DebuggableGraphQLWSHandler

            async def process_result(
                self, request: Request, result: ExecutionResult
            ) -> GraphQLHTTPResponse:
                if result_override:
                    return result_override(result)

                return await super().process_result(request, result)

        self.app = Starlite(route_handlers=[GraphQLController])
        self.client = TestClient(self.app)

    async def _graphql_request(
        self,
        method: Literal["get", "post"],
        query: Optional[str] = None,
        variables: Optional[Dict[str, object]] = None,
        files: Optional[Dict[str, BytesIO]] = None,
        headers: Optional[Dict[str, str]] = None,
        extensions: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Response:
        body = self._build_body(
            query=query, variables=variables, files=files, method=method, extensions=extensions
        )

        if body:
            if method == "get":
                kwargs["params"] = body
            else:
                if files:
                    kwargs["data"] = body
                else:
                    kwargs["content"] = json.dumps(body)

        if files:
            kwargs["files"] = files

        response = getattr(self.client, method)(
            "/graphql",
            headers=self._get_headers(method=method, headers=headers, files=files),
            **kwargs,
        )

        return Response(
            status_code=response.status_code,
            data=response.content,
            headers=response.headers,
        )

    async def request(
        self,
        url: str,
        method: Literal["get", "post", "patch", "put", "delete"],
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        response = getattr(self.client, method)(url, headers=headers)

        return Response(
            status_code=response.status_code,
            data=response.content,
            headers=response.headers,
        )

    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        return await self.request(url, "get", headers=headers)

    async def post(
        self,
        url: str,
        data: Optional[bytes] = None,
        json: Optional[JSON] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        response = self.client.post(url, headers=headers, content=data, json=json)

        return Response(
            status_code=response.status_code,
            data=response.content,
            headers=response.headers,
        )

    @contextlib.asynccontextmanager
    async def ws_connect(
        self,
        url: str,
        *,
        protocols: List[str],
    ) -> AsyncGenerator[WebSocketClient, None]:
        try:
            with self.client.websocket_connect(url, protocols) as ws:
                yield StarliteWebSocketClient(ws)
        except WebSocketDisconnect as error:
            ws = StarliteWebSocketClient(None)
            ws.handle_disconnect(error)
            yield ws


class StarliteWebSocketClient(WebSocketClient):
    def __init__(self, ws: WebSocketTestSession):
        self.ws = ws
        self._closed: bool = False
        self._close_code: Optional[int] = None
        self._close_reason: Optional[str] = None

    def handle_disconnect(self, exc: WebSocketDisconnect) -> None:
        self._closed = True
        self._close_code = exc.code
        self._close_reason = exc.reason

    async def send_json(self, payload: Dict[str, Any]) -> None:
        self.ws.send_json(payload)

    async def send_bytes(self, payload: bytes) -> None:
        self.ws.send_bytes(payload)

    async def receive(self, timeout: Optional[float] = None) -> Message:
        if self._closed:
            # if close was received via exception, fake it so that recv works
            return Message(
                type="websocket.close", data=self._close_code, extra=self._close_reason
            )
        try:
            m = self.ws.receive()
        except WebSocketDisconnect as exc:
            self._closed = True
            self._close_code = exc.code
            self._close_reason = exc.detail
            return Message(type="websocket.close", data=exc.code, extra=exc.detail)
        if m["type"] == "websocket.close":
            # Probably never happens
            self._closed = True
            self._close_code = m["code"]
            self._close_reason = m["reason"]
            return Message(type=m["type"], data=m["code"], extra=m["reason"])
        elif m["type"] == "websocket.send":
            return Message(type=m["type"], data=m["text"])
        return Message(type=m["type"], data=m["data"], extra=m["extra"])

    async def receive_json(self, timeout: Optional[float] = None) -> Any:
        m = self.ws.receive()
        assert m["type"] == "websocket.send"
        assert "text" in m
        return json.loads(m["text"])

    async def close(self) -> None:
        self.ws.close()
        self._closed = True

    @property
    def closed(self) -> bool:
        return self._closed

    @property
    def close_code(self) -> int:
        assert self._close_code is not None
        return self._close_code

    def assert_reason(self, reason: str) -> None:
        assert self._close_reason == reason
