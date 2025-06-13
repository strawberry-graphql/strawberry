from __future__ import annotations

import contextlib
import uuid
from collections.abc import AsyncGenerator
from io import BytesIO
from json import dumps
from random import randint
from typing import Any, Optional, Union
from typing_extensions import Literal

from starlette.testclient import TestClient

from sanic import Request as SanicRequest
from sanic import Sanic
from sanic import Websocket as SanicWebsocket
from strawberry.http import GraphQLHTTPResponse
from strawberry.http.ides import GraphQL_IDE
from strawberry.http.temporal_response import TemporalResponse
from strawberry.sanic.views import GraphQLView as BaseGraphQLView
from strawberry.types import ExecutionResult
from tests.http.context import get_context
from tests.views.schema import Query, schema
from tests.websockets.views import OnWSConnectMixin

from .asgi import AsgiWebSocketClient
from .base import (
    JSON,
    DebuggableGraphQLTransportWSHandler,
    DebuggableGraphQLWSHandler,
    HttpClient,
    Response,
    ResultOverrideFunction,
    WebSocketClient,
)


class GraphQLView(OnWSConnectMixin, BaseGraphQLView[dict[str, object], object]):
    result_override: ResultOverrideFunction = None
    graphql_transport_ws_handler_class = DebuggableGraphQLTransportWSHandler
    graphql_ws_handler_class = DebuggableGraphQLWSHandler

    def __init__(self, *args: Any, **kwargs: Any):
        self.result_override = kwargs.pop("result_override", None)
        super().__init__(*args, **kwargs)

    async def get_root_value(
        self, request: Union[SanicRequest, SanicWebsocket]
    ) -> Query:
        await super().get_root_value(request)  # for coverage
        return Query()

    async def get_context(
        self,
        request: Union[SanicRequest, SanicWebsocket],
        response: Union[TemporalResponse, SanicWebsocket],
    ) -> dict[str, object]:
        context = await super().get_context(request, response)

        return get_context(context)

    async def process_result(
        self, request: SanicRequest, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        if self.result_override:
            return self.result_override(result)

        return await super().process_result(request, result)


class SanicHttpClient(HttpClient):
    def __init__(
        self,
        graphiql: Optional[bool] = None,
        graphql_ide: Optional[GraphQL_IDE] = "graphiql",
        allow_queries_via_get: bool = True,
        result_override: ResultOverrideFunction = None,
        multipart_uploads_enabled: bool = False,
    ):
        self.app = Sanic(
            f"test_{int(randint(0, 1000))}",  # noqa: S311
        )
        http_view = GraphQLView.as_view(
            schema=schema,
            graphiql=graphiql,
            graphql_ide=graphql_ide,
            allow_queries_via_get=allow_queries_via_get,
            result_override=result_override,
            keep_alive=False,
            multipart_uploads_enabled=multipart_uploads_enabled,
        )
        ws_view = GraphQLView(
            schema=schema,
            graphiql=graphiql,
            graphql_ide=graphql_ide,
            allow_queries_via_get=allow_queries_via_get,
            result_override=result_override,
            keep_alive=False,
            multipart_uploads_enabled=multipart_uploads_enabled,
        )
        # self.app.add_route(http_view, "/graphql")

        # TODO: do we need the ws view here even?
        self.app.add_websocket_route(ws_view.websocket, "/graphql", subprotocols=[])

    def create_app(self, **kwargs: Any) -> None:
        self.app = Sanic(f"test-{uuid.uuid4().hex}")
        http_view = GraphQLView.as_view(schema=schema, **kwargs)
        ws_view = GraphQLView(schema=schema, **kwargs)
        # self.app.add_route(http_view, "/graphql")

        protocols = kwargs.get("subscription_protocols", [])
        self.app.add_websocket_route(
            ws_view.websocket, "/graphql", subprotocols=protocols
        )

    async def _graphql_request(
        self,
        method: Literal["get", "post"],
        query: Optional[str] = None,
        variables: Optional[dict[str, object]] = None,
        files: Optional[dict[str, BytesIO]] = None,
        headers: Optional[dict[str, str]] = None,
        extensions: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Response:
        body = self._build_body(
            query=query,
            variables=variables,
            files=files,
            method=method,
            extensions=extensions,
        )

        if body:
            if method == "get":
                kwargs["params"] = body
            elif files:
                kwargs["data"] = body
            else:
                kwargs["content"] = dumps(body)

        request, response = await self.app.asgi_client.request(
            method,
            "/graphql",
            headers=self._get_headers(method=method, headers=headers, files=files),
            files=files,
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
        headers: Optional[dict[str, str]] = None,
    ) -> Response:
        request, response = await self.app.asgi_client.request(
            method,
            url,
            headers=headers,
        )

        return Response(
            status_code=response.status_code,
            data=response.content,
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
        body = data or dumps(json)
        request, response = await self.app.asgi_client.request(
            "post", url, content=body, headers=headers
        )

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
        protocols: list[str],
    ) -> AsyncGenerator[WebSocketClient, None]:
        with TestClient(self.app) as client:
            with client.websocket_connect(url, protocols) as ws:
                yield AsgiWebSocketClient(ws)
