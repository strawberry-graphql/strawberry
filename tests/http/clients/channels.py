from __future__ import annotations

import contextlib
import json as json_module
from io import BytesIO
from typing import Any, AsyncGenerator, Dict, List, Optional
from typing_extensions import Literal

from urllib3 import encode_multipart_formdata

from channels.testing import HttpCommunicator, WebsocketCommunicator
from strawberry.channels import (
    GraphQLHTTPConsumer,
    GraphQLWSConsumer,
    SyncGraphQLHTTPConsumer,
)
from strawberry.channels.handlers.base import ChannelsConsumer
from strawberry.http import GraphQLHTTPResponse
from strawberry.http.ides import GraphQL_IDE
from strawberry.http.typevars import Context, RootValue
from tests.views.schema import Query, schema

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
        body["variables"] = json_module.dumps(variables)

    parts = [f"{k}={v}" for k, v in body.items()]
    return f"{path}?{'&'.join(parts)}"


def create_multipart_request_body(
    body: Dict[str, object], files: Dict[str, BytesIO]
) -> tuple[list[tuple[str, str]], bytes]:
    fields = {
        "operations": body["operations"],
        "map": body["map"],
    }

    for filename, data in files.items():
        fields[filename] = (filename, data.read().decode(), "text/plain")

    request_body, content_type_header = encode_multipart_formdata(fields)

    headers = [
        ("Content-Type", content_type_header),
        ("Content-Length", f"{len(request_body)}"),
    ]

    return headers, request_body


class DebuggableGraphQLTransportWSConsumer(GraphQLWSConsumer):
    def get_tasks(self) -> List[Any]:
        if hasattr(self._handler, "operations"):
            return [op.task for op in self._handler.operations.values()]
        else:
            return list(self._handler.tasks.values())

    async def get_context(self, *args: str, **kwargs: Any) -> object:
        context = await super().get_context(*args, **kwargs)
        context["ws"] = self._handler._ws
        context["get_tasks"] = self.get_tasks
        context["connectionInitTimeoutTask"] = getattr(
            self._handler, "connection_init_timeout_task", None
        )
        for key, val in get_context({}).items():
            context[key] = val
        return context


class DebuggableGraphQLHTTPConsumer(GraphQLHTTPConsumer):
    result_override: ResultOverrideFunction = None

    def __init__(self, *args: Any, **kwargs: Any):
        self.result_override = kwargs.pop("result_override")
        super().__init__(*args, **kwargs)

    async def get_root_value(self, request: ChannelsConsumer) -> Optional[RootValue]:
        return Query()

    async def get_context(self, request: ChannelsConsumer, response: Any) -> Context:
        context = await super().get_context(request, response)

        return get_context(context)

    async def process_result(
        self, request: ChannelsConsumer, result: Any
    ) -> GraphQLHTTPResponse:
        if self.result_override:
            return self.result_override(result)

        return await super().process_result(request, result)


class DebuggableSyncGraphQLHTTPConsumer(SyncGraphQLHTTPConsumer):
    result_override: ResultOverrideFunction = None

    def __init__(self, *args: Any, **kwargs: Any):
        self.result_override = kwargs.pop("result_override")
        super().__init__(*args, **kwargs)

    def get_root_value(self, request: ChannelsConsumer) -> Optional[RootValue]:
        return Query()

    def get_context(self, request: ChannelsConsumer, response: Any) -> Context:
        context = super().get_context(request, response)

        return get_context(context)

    def process_result(
        self, request: ChannelsConsumer, result: Any
    ) -> GraphQLHTTPResponse:
        if self.result_override:
            return self.result_override(result)

        return super().process_result(request, result)


class ChannelsHttpClient(HttpClient):
    """
    A client to test websockets over channels
    """

    def __init__(
        self,
        graphiql: Optional[bool] = None,
        graphql_ide: Optional[GraphQL_IDE] = "graphiql",
        allow_queries_via_get: bool = True,
        result_override: ResultOverrideFunction = None,
    ):
        self.ws_app = DebuggableGraphQLTransportWSConsumer.as_asgi(
            schema=schema,
            keep_alive=False,
        )

        self.http_app = DebuggableGraphQLHTTPConsumer.as_asgi(
            schema=schema,
            graphiql=graphiql,
            graphql_ide=graphql_ide,
            allow_queries_via_get=allow_queries_via_get,
            result_override=result_override,
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
        extensions: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Response:
        body = self._build_body(
            query=query, variables=variables, files=files, method=method, extensions=extensions
        )

        headers = self._get_headers(method=method, headers=headers, files=files)

        if method == "post":
            if files:
                new_headers, body = create_multipart_request_body(body, files)
                for k, v in new_headers:
                    headers[k] = v
            else:
                body = json_module.dumps(body).encode()
            endpoint_url = "/graphql"
        else:
            body = b""
            endpoint_url = generate_get_path("/graphql", query, variables)

        return await self.request(
            url=endpoint_url, method=method, body=body, headers=headers
        )

    async def request(
        self,
        url: str,
        method: Literal["get", "post", "patch", "put", "delete"],
        body: bytes = b"",
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        # HttpCommunicator expects tuples of bytestrings
        if headers:
            headers = [(k.encode(), v.encode()) for k, v in headers.items()]

        communicator = HttpCommunicator(
            self.http_app,
            method.upper(),
            url,
            body=body,
            headers=headers,
        )
        response = await communicator.get_response()

        return Response(
            status_code=response["status"],
            data=response["body"],
            headers={k.decode(): v.decode() for k, v in response["headers"]},
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
        body = b""
        if data is not None:
            body = data
        elif json is not None:
            body = json_module.dumps(json).encode()
        return await self.request(url, "post", body=body, headers=headers)

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


class SyncChannelsHttpClient(ChannelsHttpClient):
    def __init__(
        self,
        graphiql: Optional[bool] = None,
        graphql_ide: Optional[GraphQL_IDE] = "graphiql",
        allow_queries_via_get: bool = True,
        result_override: ResultOverrideFunction = None,
    ):
        self.http_app = DebuggableSyncGraphQLHTTPConsumer.as_asgi(
            schema=schema,
            graphiql=graphiql,
            graphql_ide=graphql_ide,
            allow_queries_via_get=allow_queries_via_get,
            result_override=result_override,
        )


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
        return json_module.loads(m["text"])

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
