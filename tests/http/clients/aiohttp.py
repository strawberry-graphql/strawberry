from __future__ import annotations

import contextlib
import json
from collections.abc import AsyncGenerator, Mapping
from io import BytesIO
from typing import Any, Optional, Union
from typing_extensions import Literal

from aiohttp import web
from aiohttp.client_ws import ClientWebSocketResponse
from aiohttp.http_websocket import WSMsgType
from aiohttp.test_utils import TestClient, TestServer
from strawberry.aiohttp.views import GraphQLView as BaseGraphQLView
from strawberry.http import GraphQLHTTPResponse
from strawberry.http.ides import GraphQL_IDE
from strawberry.types import ExecutionResult
from tests.http.context import get_context
from tests.views.schema import Query, schema
from tests.websockets.views import OnWSConnectMixin

from .base import (
    JSON,
    DebuggableGraphQLTransportWSHandler,
    DebuggableGraphQLWSHandler,
    HttpClient,
    Message,
    Response,
    ResultOverrideFunction,
    WebSocketClient,
)


class GraphQLView(OnWSConnectMixin, BaseGraphQLView[dict[str, object], object]):
    result_override: ResultOverrideFunction = None
    graphql_transport_ws_handler_class = DebuggableGraphQLTransportWSHandler
    graphql_ws_handler_class = DebuggableGraphQLWSHandler

    async def get_context(
        self, request: web.Request, response: Union[web.Response, web.WebSocketResponse]
    ) -> dict[str, object]:
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
        multipart_uploads_enabled: bool = False,
    ):
        view = GraphQLView(
            schema=schema,
            graphiql=graphiql,
            graphql_ide=graphql_ide,
            allow_queries_via_get=allow_queries_via_get,
            keep_alive=False,
            multipart_uploads_enabled=multipart_uploads_enabled,
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
        query: str,
        variables: Optional[dict[str, object]] = None,
        files: Optional[dict[str, BytesIO]] = None,
        headers: Optional[dict[str, str]] = None,
        **kwargs: Any,
    ) -> Response:
        async with TestClient(TestServer(self.app)) as client:
            body = self._build_body(
                query=query, variables=variables, files=files, method=method
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
        headers: Optional[dict[str, str]] = None,
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
        headers: Optional[dict[str, str]] = None,
    ) -> Response:
        return await self.request(url, "get", headers=headers)

    async def post(
        self,
        url: str,
        data: Optional[bytes] = None,
        json: Optional[JSON] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> Response:
        async with TestClient(TestServer(self.app)) as client:
            response = await client.post(
                "/graphql", headers=headers, data=data, json=json
            )

            return Response(
                status_code=response.status,
                data=(await response.text()).encode(),
                headers=dict(response.headers),
            )

    @contextlib.asynccontextmanager
    async def ws_connect(
        self,
        url: str,
        *,
        protocols: list[str],
    ) -> AsyncGenerator[WebSocketClient, None]:
        async with (
            TestClient(TestServer(self.app)) as client,
            client.ws_connect(url, protocols=protocols) as ws,
        ):
            yield AioWebSocketClient(ws)


class AioWebSocketClient(WebSocketClient):
    def __init__(self, ws: ClientWebSocketResponse):
        self.ws = ws
        self._reason: Optional[str] = None

    async def send_text(self, payload: str) -> None:
        await self.ws.send_str(payload)

    async def send_json(self, payload: Mapping[str, object]) -> None:
        await self.ws.send_json(payload)

    async def send_bytes(self, payload: bytes) -> None:
        await self.ws.send_bytes(payload)

    async def receive(self, timeout: Optional[float] = None) -> Message:
        m = await self.ws.receive(timeout)
        self._reason = m.extra
        return Message(type=m.type, data=m.data, extra=m.extra)

    async def receive_json(self, timeout: Optional[float] = None) -> object:
        m = await self.ws.receive(timeout)
        assert m.type == WSMsgType.TEXT
        return json.loads(m.data)

    async def close(self) -> None:
        await self.ws.close()

    @property
    def accepted_subprotocol(self) -> Optional[str]:
        return self.ws.protocol

    @property
    def closed(self) -> bool:
        return self.ws.closed

    @property
    def close_code(self) -> int:
        assert self.ws.close_code is not None
        return self.ws.close_code

    @property
    def close_reason(self) -> Optional[str]:
        return self._reason
