from __future__ import annotations

import contextlib
import json
from io import BytesIO
from typing import Any, AsyncGenerator, Dict, List, Optional, Union
from typing_extensions import Literal

from starlette.requests import Request
from starlette.responses import Response as StarletteResponse
from starlette.testclient import TestClient
from starlette.websockets import WebSocket, WebSocketDisconnect

from strawberry.asgi import GraphQL as BaseGraphQLView
from strawberry.asgi.handlers import GraphQLTransportWSHandler, GraphQLWSHandler
from strawberry.http import GraphQLHTTPResponse
from strawberry.http.ides import GraphQL_IDE
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


class DebuggableGraphQLTransportWSHandler(
    DebuggableGraphQLTransportWSMixin, GraphQLTransportWSHandler
):
    pass


class DebuggableGraphQLWSHandler(DebuggableGraphQLWSMixin, GraphQLWSHandler):
    pass


class GraphQLView(BaseGraphQLView):
    result_override: ResultOverrideFunction = None
    graphql_transport_ws_handler_class = DebuggableGraphQLTransportWSHandler
    graphql_ws_handler_class = DebuggableGraphQLWSHandler

    async def get_root_value(self, request: Union[WebSocket, Request]) -> Query:
        return Query()

    async def get_context(
        self,
        request: Union[Request, WebSocket],
        response: Optional[StarletteResponse] = None,
    ) -> object:
        context = await super().get_context(request, response)

        return get_context(context)

    async def process_result(
        self, request: Request, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        if self.result_override:
            return self.result_override(result)

        return await super().process_result(request, result)


class AsgiHttpClient(HttpClient):
    def __init__(
        self,
        graphiql: Optional[bool] = None,
        graphql_ide: Optional[GraphQL_IDE] = "graphiql",
        allow_queries_via_get: bool = True,
        result_override: ResultOverrideFunction = None,
    ):
        view = GraphQLView(
            schema,
            graphiql=graphiql,
            graphql_ide=graphql_ide,
            allow_queries_via_get=allow_queries_via_get,
            keep_alive=False,
        )
        view.result_override = result_override

        self.client = TestClient(view)

    def create_app(self, **kwargs: Any) -> None:
        view = GraphQLView(schema=schema, **kwargs)
        self.client = TestClient(view)

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
            query=query, variables=variables, files=files, method=method
        )

        if method == "get":
            kwargs["params"] = body
        elif body:
            if files:
                kwargs["data"] = body
            else:
                kwargs["content"] = json.dumps(body)

        if files is not None:
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
                yield AsgiWebSocketClient(ws)
        except WebSocketDisconnect as error:
            ws = AsgiWebSocketClient(None)
            ws.handle_disconnect(error)
            yield ws


class AsgiWebSocketClient(WebSocketClient):
    def __init__(self, ws: Any):
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
        m = self.ws.receive()
        if m["type"] == "websocket.close":
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
