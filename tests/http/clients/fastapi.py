from __future__ import annotations

import contextlib
import json
from io import BytesIO
from typing import Any, AsyncGenerator, Dict, List, Optional
from typing_extensions import Literal

from starlette.websockets import WebSocketDisconnect

from fastapi import BackgroundTasks, Depends, FastAPI, Request, WebSocket
from fastapi.testclient import TestClient
from strawberry.fastapi import GraphQLRouter as BaseGraphQLRouter
from strawberry.fastapi.handlers import GraphQLTransportWSHandler, GraphQLWSHandler
from strawberry.http import GraphQLHTTPResponse
from strawberry.http.ides import GraphQL_IDE
from strawberry.types import ExecutionResult
from tests.views.schema import Query, schema

from ..context import get_context
from .asgi import AsgiWebSocketClient
from .base import (
    JSON,
    DebuggableGraphQLTransportWSMixin,
    DebuggableGraphQLWSMixin,
    HttpClient,
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


def custom_context_dependency() -> str:
    return "Hi!"


async def fastapi_get_context(
    background_tasks: BackgroundTasks,
    request: Request = None,  # type: ignore
    ws: WebSocket = None,  # type: ignore
    custom_value: str = Depends(custom_context_dependency),
) -> Dict[str, object]:
    return get_context(
        {
            "request": request or ws,
            "background_tasks": background_tasks,
        }
    )


async def get_root_value(
    request: Request = None,  # type: ignore - FastAPI
    ws: WebSocket = None,  # type: ignore - FastAPI
) -> Query:
    return Query()


class GraphQLRouter(BaseGraphQLRouter[Any, Any]):
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
        )
        graphql_app.result_override = result_override
        self.app.include_router(graphql_app, prefix="/graphql")

        self.client = TestClient(self.app)

    def create_app(self, **kwargs: Any) -> None:
        self.app = FastAPI()
        graphql_app = GraphQLRouter(schema=schema, **kwargs)
        self.app.include_router(graphql_app, prefix="/graphql")

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
                yield AsgiWebSocketClient(ws)
        except WebSocketDisconnect as error:
            ws = AsgiWebSocketClient(None)
            ws.handle_disconnect(error)
            yield ws
