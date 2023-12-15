from __future__ import annotations

import contextlib
import json
from io import BytesIO
from typing import Any, AsyncGenerator, Dict, List, Optional
from typing_extensions import Literal

from aiohttp import web
from aiohttp.client_ws import ClientWebSocketResponse
from aiohttp.http_websocket import WSMsgType
from aiohttp.test_utils import TestClient, TestServer
from strawberry.aiohttp.handlers import GraphQLTransportWSHandler, GraphQLWSHandler
from strawberry.aiohttp.views import GraphQLView as BaseGraphQLView
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

    async def get_context(
        self, request: web.Request, response: web.StreamResponse
    ) -> object:
        context = await super().get_context(request, response)

        return get_context(context)

    async def get_root_value(self, request: web.Request) -> Query:
        await super().get_root_value(request)  # for coverage
        return Query()

    async def process_result(
        self, request: web.Request, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        if self.result_override:
            return self.result_override(result)

        return await super().process_result(request, result)


class AioHttpClient(HttpClient):
    def __init__(
        self,
        graphiql: Optional[bool] = None,
        graphql_ide: Optional[GraphQL_IDE] = "graphiql",
        allow_queries_via_get: bool = True,
        result_override: ResultOverrideFunction = None,
    ):
        view = GraphQLView(
            schema=schema,
            graphiql=graphiql,
            graphql_ide=graphql_ide,
            allow_queries_via_get=allow_queries_via_get,
            keep_alive=False,
        )
        view.result_override = result_override

        self.app = web.Application()
        self.app.router.add_route(
            "*",
            "/graphql",
            view,
        )

    def create_app(self, **kwargs: Any) -> None:
        view = GraphQLView(schema=schema, **kwargs)

        self.app = web.Application()
        self.app.router.add_route(
            "*",
            "/graphql",
            view,
        )

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
        async with TestClient(TestServer(self.app)) as client:
            body = self._build_body(
                query=query, variables=variables, files=files, method=method, extensions=extensions
            )

            if body and files:
                body.update(files)

            if method == "get":
                kwargs["params"] = body
            else:
                kwargs["data"] = body if files else json.dumps(body)

            response = await getattr(client, method)(
                "/graphql",
                headers=self._get_headers(method=method, headers=headers, files=files),
                **kwargs,
            )

            return Response(
                status_code=response.status,
                data=(await response.text()).encode(),
                headers=response.headers,
            )

    async def request(
        self,
        url: str,
        method: Literal["get", "post", "patch", "put", "delete"],
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        async with TestClient(TestServer(self.app)) as client:
            response = await getattr(client, method)(url, headers=headers)

            return Response(
                status_code=response.status,
                data=(await response.text()).encode(),
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
        async with TestClient(TestServer(self.app)) as client:
            response = await client.post(
                "/graphql", headers=headers, data=data, json=json
            )

            return Response(
                status_code=response.status,
                data=(await response.text()).encode(),
                headers=response.headers,
            )

    @contextlib.asynccontextmanager
    async def ws_connect(
        self,
        url: str,
        *,
        protocols: List[str],
    ) -> AsyncGenerator[WebSocketClient, None]:
        server = TestServer(self.app)
        await server.start_server()
        client = TestClient(server)
        async with client.ws_connect(url, protocols=protocols) as ws:
            yield AioWebSocketClient(ws)


class AioWebSocketClient(WebSocketClient):
    def __init__(self, ws: ClientWebSocketResponse):
        self.ws = ws
        self._reason: Optional[str] = None

    async def send_json(self, payload: Dict[str, Any]) -> None:
        await self.ws.send_json(payload)

    async def send_bytes(self, payload: bytes) -> None:
        await self.ws.send_bytes(payload)

    async def receive(self, timeout: Optional[float] = None) -> Message:
        m = await self.ws.receive(timeout)
        self._reason = m.extra
        return Message(type=m.type, data=m.data, extra=m.extra)

    async def receive_json(self, timeout: Optional[float] = None) -> Any:
        m = await self.ws.receive(timeout)
        assert m.type == WSMsgType.TEXT
        return json.loads(m.data)

    async def close(self) -> None:
        await self.ws.close()

    @property
    def closed(self) -> bool:
        return self.ws.closed

    @property
    def close_code(self) -> int:
        assert self.ws.close_code is not None
        return self.ws.close_code

    def assert_reason(self, reason: str) -> None:
        assert self._reason == reason
