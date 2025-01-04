from __future__ import annotations

import contextlib
import json
from collections.abc import AsyncGenerator
from io import BytesIO
from typing import Any, Optional
from typing_extensions import Literal

from fastapi import BackgroundTasks, Depends, FastAPI, Request, WebSocket
from fastapi.testclient import TestClient
from strawberry.fastapi import GraphQLRouter as BaseGraphQLRouter
from strawberry.http import GraphQLHTTPResponse
from strawberry.http.ides import GraphQL_IDE
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


def custom_context_dependency() -> str:
    return "Hi!"


def fastapi_get_context(
    background_tasks: BackgroundTasks,
    request: Request = None,  # type: ignore
    ws: WebSocket = None,  # type: ignore
    custom_value: str = Depends(custom_context_dependency),
) -> dict[str, object]:
    return get_context(
        {
            "request": request or ws,
            "background_tasks": background_tasks,
        }
    )


def get_root_value(
    request: Request = None,  # type: ignore - FastAPI
    ws: WebSocket = None,  # type: ignore - FastAPI
) -> Query:
    return Query()


class GraphQLRouter(OnWSConnectMixin, BaseGraphQLRouter[dict[str, object], object]):
    result_override: ResultOverrideFunction = None
    graphql_transport_ws_handler_class = DebuggableGraphQLTransportWSHandler
    graphql_ws_handler_class = DebuggableGraphQLWSHandler

    async def process_result(
        self, request: Request, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        if self.result_override:
            return self.result_override(result)

        return await super().process_result(request, result)


class FastAPIHttpClient(HttpClient):
    def __init__(
        self,
        graphiql: Optional[bool] = None,
        graphql_ide: Optional[GraphQL_IDE] = "graphiql",
        allow_queries_via_get: bool = True,
        result_override: ResultOverrideFunction = None,
        multipart_uploads_enabled: bool = False,
    ):
        self.app = FastAPI()

        graphql_app = GraphQLRouter(
            schema,
            graphiql=graphiql,
            graphql_ide=graphql_ide,
            context_getter=fastapi_get_context,
            root_value_getter=get_root_value,
            allow_queries_via_get=allow_queries_via_get,
            keep_alive=False,
            multipart_uploads_enabled=multipart_uploads_enabled,
        )
        graphql_app.result_override = result_override
        self.app.include_router(graphql_app, prefix="/graphql")

        self.client = TestClient(self.app)

    def create_app(self, **kwargs: Any) -> None:
        self.app = FastAPI()
        graphql_app = GraphQLRouter(schema=schema, **kwargs)
        self.app.include_router(graphql_app, prefix="/graphql")

        self.client = TestClient(self.app)

    async def _handle_response(self, response: Any) -> Response:
        # TODO: here we should handle the stream
        return Response(
            status_code=response.status_code,
            data=response.content,
            headers=response.headers,
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
        body = self._build_body(
            query=query, variables=variables, files=files, method=method
        )

        if body:
            if method == "get":
                kwargs["params"] = body
            elif files:
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

        return await self._handle_response(response)

    async def request(
        self,
        url: str,
        method: Literal["get", "post", "patch", "put", "delete"],
        headers: Optional[dict[str, str]] = None,
    ) -> Response:
        response = getattr(self.client, method)(url, headers=headers)

        return await self._handle_response(response)

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
        response = self.client.post(url, headers=headers, content=data, json=json)

        return await self._handle_response(response)

    @contextlib.asynccontextmanager
    async def ws_connect(
        self,
        url: str,
        *,
        protocols: list[str],
    ) -> AsyncGenerator[WebSocketClient, None]:
        with self.client.websocket_connect(url, protocols) as ws:
            yield AsgiWebSocketClient(ws)
