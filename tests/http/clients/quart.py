import asyncio
import contextlib
import json
import urllib.parse
from collections.abc import AsyncGenerator, Mapping
from io import BytesIO
from typing import Any, Optional, AsyncGenerator, Mapping, Union

from asgiref.typing import ASGISendEvent
from hypercorn.typing import WebsocketScope
from quart.typing import TestWebsocketConnectionProtocol
from quart.utils import decode_headers
from typing import Any, Optional
from typing_extensions import Literal

from quart import Quart
from quart import Request as QuartRequest
from quart import Response as QuartResponse
from quart.datastructures import FileStorage
from quart.testing.connections import TestWebsocketConnection

from strawberry.exceptions import ConnectionRejectionError
from strawberry.http import GraphQLHTTPResponse
from strawberry.http.ides import GraphQL_IDE
from strawberry.quart.views import GraphQLView as BaseGraphQLView
from strawberry.types import ExecutionResult
from strawberry.types.unset import UnsetType, UNSET
from tests.http.context import get_context
from tests.views.schema import Query, schema

from .base import (
    JSON,
    HttpClient,
    Message,
    Response,
    ResultOverrideFunction,
    WebSocketClient,
    DebuggableGraphQLTransportWSHandler,
    DebuggableGraphQLWSHandler
)


class GraphQLView(BaseGraphQLView[dict[str, object], object]):
    methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"]
    graphql_transport_ws_handler_class = DebuggableGraphQLTransportWSHandler
    graphql_ws_handler_class = DebuggableGraphQLWSHandler
    result_override: ResultOverrideFunction = None

    def __init__(self, *args: Any, **kwargs: Any):
        self.result_override = kwargs.pop("result_override", None)
        super().__init__(*args, **kwargs)

    async def get_root_value(self, request: QuartRequest) -> Query:
        await super().get_root_value(request)  # for coverage
        return Query()

    async def get_context(
        self, request: QuartRequest, response: QuartResponse
    ) -> dict[str, object]:
        context = await super().get_context(request, response)

        return get_context(context)

    async def process_result(
        self, request: QuartRequest, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        if self.result_override:
            return self.result_override(result)

        return await super().process_result(request, result)

    async def on_ws_connect(
        self, context: dict[str, object]
    ) -> Union[UnsetType, None, dict[str, object]]:
        connection_params = context["connection_params"]

        if isinstance(connection_params, dict):
            if connection_params.get("test-reject"):
                if "err-payload" in connection_params:
                    raise ConnectionRejectionError(connection_params["err-payload"])
                raise ConnectionRejectionError

            if connection_params.get("test-accept"):
                if "ack-payload" in connection_params:
                    return connection_params["ack-payload"]
                return UNSET

            if connection_params.get("test-modify"):
                connection_params["modified"] = True
                return UNSET

        return await super().on_ws_connect(context)


class QuartHttpClient(HttpClient):
    def __init__(
        self,
        graphiql: Optional[bool] = None,
        graphql_ide: Optional[GraphQL_IDE] = "graphiql",
        allow_queries_via_get: bool = True,
        result_override: ResultOverrideFunction = None,
        multipart_uploads_enabled: bool = False,
    ):
        self.app = Quart(__name__)
        self.app.debug = True

        view = GraphQLView.as_view(
            "graphql_view",
            schema=schema,
            graphiql=graphiql,
            graphql_ide=graphql_ide,
            allow_queries_via_get=allow_queries_via_get,
            result_override=result_override,
            multipart_uploads_enabled=multipart_uploads_enabled,
        )

        self.app.add_url_rule(
            "/graphql",
            view_func=view,
        )
        self.app.add_url_rule(
            "/graphql", view_func=view, methods=["GET"], websocket=True
        )

    def create_app(self, **kwargs: Any) -> None:
        self.app = Quart(__name__)
        self.app.debug = True

        view = GraphQLView.as_view("graphql_view", schema=schema, **kwargs)

        self.app.add_url_rule(
            "/graphql",
            view_func=view,
        )
        self.app.add_url_rule(
            "/graphql", view_func=view, methods=["GET"], websocket=True
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

        url = "/graphql"

        if method == "get":
            body_encoded = urllib.parse.urlencode(body or {})
            url = f"{url}?{body_encoded}"
        elif body:
            if files:
                kwargs["form"] = body
                kwargs["files"] = {
                    k: FileStorage(v, filename=k) for k, v in files.items()
                }
            else:
                kwargs["data"] = json.dumps(body)

        headers = self._get_headers(method=method, headers=headers, files=files)

        return await self.request(url, method, headers=headers, **kwargs)

    async def request(
        self,
        url: str,
        method: Literal["get", "post", "patch", "put", "delete"],
        headers: Optional[dict[str, str]] = None,
        **kwargs: Any,
    ) -> Response:
        async with self.app.test_app() as test_app, self.app.app_context():
            client = test_app.test_client()
            response = await getattr(client, method)(url, headers=headers, **kwargs)

        return Response(
            status_code=response.status_code,
            data=(await response.data),
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
        kwargs = {"headers": headers, "data": data, "json": json}
        return await self.request(
            url, "post", **{k: v for k, v in kwargs.items() if v is not None}
        )

    @contextlib.asynccontextmanager
    async def ws_connect(
        self,
        url: str,
        *,
        protocols: list[str],
    ) -> AsyncGenerator[WebSocketClient, None]:
        headers = {
            'sec-websocket-protocol': ", ".join(protocols),
        }
        async with self.app.test_app() as test_app:
            client = test_app.test_client()
            client.websocket_connection_class = QuartTestWebsocketConnection
            async with client.websocket(url, headers=headers, subprotocols=protocols) as ws:
                yield QuartWebSocketClient(ws)

class QuartTestWebsocketConnection(TestWebsocketConnection):
    def __init__(self, app: Quart, scope: WebsocketScope) -> None:
        scope['asgi'] = {'spec_version': '2.3'}
        super().__init__(app, scope)

    async def _asgi_send(self, message: ASGISendEvent) -> None:
        if message["type"] == "websocket.accept":
            self.accepted = True
        elif message["type"] == "websocket.send":
            await self._receive_queue.put(message.get("bytes") or message.get("text"))
        elif message["type"] == "websocket.http.response.start":
            self.headers = decode_headers(message["headers"])
            self.status_code = message["status"]
        elif message["type"] == "websocket.http.response.body":
            self.response_data.extend(message["body"])
        elif message["type"] == "websocket.close":
            await self._receive_queue.put(json.dumps(message))

class QuartWebSocketClient(WebSocketClient):
    def __init__(self, ws: TestWebsocketConnectionProtocol):
        self.ws = ws
        self._closed: bool = False
        self._close_code: Optional[int] = None
        self._close_reason: Optional[str] = None

    async def send_text(self, payload: str) -> None:
        await self.ws.send(payload)

    async def send_json(self, payload: Mapping[str, object]) -> None:
        await self.ws.send_json(payload)

    async def send_bytes(self, payload: bytes) -> None:
        await self.ws.send(payload)

    async def receive(self, timeout: Optional[float] = None) -> Message:
        if self._closed:
            # if close was received via exception, fake it so that recv works
            return Message(
                type="websocket.close", data=self._close_code, extra=self._close_reason
            )
        m = await asyncio.wait_for(self.ws.receive_json(), timeout=timeout)
        if m["type"] == "websocket.close":
            self._closed = True
            self._close_code = m["code"]
            self._close_reason = m.get("reason", None)
            return Message(type=m["type"], data=m["code"], extra=m.get("reason", None))
        if m["type"] == "websocket.send":
            return Message(type=m["type"], data=m["text"])
        if m['type'] == "connection_ack":
            return Message(type=m['type'], data='')
        return Message(type=m["type"], data=m["data"], extra=m["extra"])

    async def receive_json(self, timeout: Optional[float] = None) -> Any:
        m =  await asyncio.wait_for(self.ws.receive_json(), timeout=timeout)
        return m

    async def close(self) -> None:
        await self.ws.close(1000)
        self._closed = True

    @property
    def accepted_subprotocol(self) -> Optional[str]:
        return ""

    @property
    def closed(self) -> bool:
        return self._closed

    @property
    def close_code(self) -> int:
        assert self._close_code is not None
        return self._close_code

    @property
    def close_reason(self) -> Optional[str]:
        return self._close_reason
