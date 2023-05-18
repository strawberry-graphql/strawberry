from __future__ import annotations

import contextlib
import json
from io import BytesIO
from typing import Any, AsyncGenerator, Dict, List, Optional
from typing_extensions import Literal

from channels.testing import HttpCommunicator, WebsocketCommunicator
from strawberry.channels import GraphQLHTTPConsumer, GraphQLWSConsumer
from tests.views.schema import schema

from ..context import get_context
from .base import (
    JSON,
    HttpClient,
    Message,
    Response,
    ResultOverrideFunction,
    WebSocketClient,
)


def generate_get_path(
    path, query: str, variables: Optional[Dict[str, Any]] = None
) -> str:
    body: Dict[str, Any] = {"query": query}
    if variables is not None:
        body["variables"] = json.dumps(variables)

    parts = [f"{k}={v}" for k, v in body.items()]
    return f"{path}?{'&'.join(parts)}"


class DebuggableGraphQLTransportWSConsumer(GraphQLWSConsumer):
    async def get_context(self, *args: str, **kwargs: Any) -> object:
        context = await super().get_context(*args, **kwargs)
        context.tasks = self._handler.tasks
        context.connectionInitTimeoutTask = getattr(
            self._handler, "connection_init_timeout_task", None
        )
        for key, val in get_context({}).items():
            setattr(context, key, val)
        return context


class ChannelsHttpClient(HttpClient):
    """
    A client to test websockets over channels
    """

    def __init__(
        self,
        graphiql: bool = True,
        allow_queries_via_get: bool = True,
        result_override: ResultOverrideFunction = None,
    ):
        self.ws_app = DebuggableGraphQLTransportWSConsumer.as_asgi(
            schema=schema,
            keep_alive=False,
        )
        self.http_app = GraphQLHTTPConsumer.as_asgi(
            schema=schema,
            graphiql=graphiql,
            allow_queries_via_get=allow_queries_via_get,
        )

    def create_app(self, **kwargs: Any) -> None:
        self.ws_app = DebuggableGraphQLTransportWSConsumer.as_asgi(
            schema=schema, **kwargs
        )

    async def _graphql_request(
        self,
        method: Literal["get", "post"],
        query: Optional[str] = None,
        variables: Optional[Dict[str, object]] = None,
        files: Optional[Dict[str, BytesIO]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> Response:
        body = self._build_body(
            query=query, variables=variables, files=files, method=method
        )

        # if method == "get":
        #     if files:

        if files is not None:
            kwargs["files"] = files

        headers = self._get_headers(method=method, headers=headers, files=files)
        headers = [
            (k.encode(), v.encode()) for k, v in headers.items()
        ]  # HttpCommunicator expects tuples of bytestrings

        if method == "post":
            body = json.dumps(body).encode()
            endpoint_url = "/graphql"
        else:
            body = b""
            endpoint_url = generate_get_path("/graphql", query, variables)

        communicator = HttpCommunicator(
            self.http_app,
            method.upper(),
            endpoint_url,
            body=body,
            headers=headers,
        )
        response = await communicator.get_response()

        return Response(
            status_code=response["status"],
            data=response["body"],
            headers=response["headers"],
        )

    async def request(
        self,
        url: str,
        method: Literal["get", "post", "patch", "put", "delete"],
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        communicator = HttpCommunicator(
            self.http_app,
            method.upper(),
            url,
            headers=headers,
        )
        response = await communicator.get_response()

        return Response(
            status_code=response["status"],
            data=response["body"].decode(),
            headers=response["headers"],
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
        client = WebsocketCommunicator(self.ws_app, url, subprotocols=protocols)

        res = await client.connect()
        assert res == (True, protocols[0])
        try:
            yield ChannelsWebSocketClient(client)
        finally:
            await client.disconnect()


class ChannelsWebSocketClient(WebSocketClient):
    def __init__(self, client: WebsocketCommunicator):
        self.ws = client
        self._closed: bool = False
        self._close_code: Optional[int] = None
        self._close_reason: Optional[str] = None

    def name(self) -> str:
        return "channels"

    async def send_json(self, payload: Dict[str, Any]) -> None:
        await self.ws.send_json_to(payload)

    async def send_bytes(self, payload: bytes) -> None:
        await self.ws.send_to(bytes_data=payload)

    async def receive(self, timeout: Optional[float] = None) -> Message:
        m = await self.ws.receive_output(timeout=timeout)
        if m["type"] == "websocket.close":
            self._closed = True
            self._close_code = m["code"]
            self._close_reason = m.get("reason")
            return Message(type=m["type"], data=m["code"], extra=m.get("reason"))
        elif m["type"] == "websocket.send":
            return Message(type=m["type"], data=m["text"])
        return Message(type=m["type"], data=m["data"], extra=m["extra"])

    async def receive_json(self, timeout: Optional[float] = None) -> Any:
        m = await self.ws.receive_output(timeout=timeout)
        assert m["type"] == "websocket.send"
        assert "text" in m
        return json.loads(m["text"])

    async def close(self) -> None:
        await self.ws.disconnect()
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
