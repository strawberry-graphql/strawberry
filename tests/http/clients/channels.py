from __future__ import annotations

import contextlib
import json as json_module
from collections.abc import AsyncGenerator, Mapping
from io import BytesIO
from typing import Any, Optional
from typing_extensions import Literal

from urllib3 import encode_multipart_formdata

from channels.testing import HttpCommunicator, WebsocketCommunicator
from strawberry.channels import (
    GraphQLHTTPConsumer,
    GraphQLWSConsumer,
    SyncGraphQLHTTPConsumer,
)
from strawberry.channels.handlers.http_handler import ChannelsRequest
from strawberry.http import GraphQLHTTPResponse
from strawberry.http.ides import GraphQL_IDE
from strawberry.http.temporal_response import TemporalResponse
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


def generate_get_path(
    path, query: str, variables: Optional[dict[str, Any]] = None
) -> str:
    body: dict[str, Any] = {"query": query}
    if variables is not None:
        body["variables"] = json_module.dumps(variables)

    parts = [f"{k}={v}" for k, v in body.items()]
    return f"{path}?{'&'.join(parts)}"


def create_multipart_request_body(
    body: dict[str, object], files: dict[str, BytesIO]
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


class DebuggableGraphQLHTTPConsumer(GraphQLHTTPConsumer[dict[str, object], object]):
    result_override: ResultOverrideFunction = None

    def __init__(self, *args: Any, **kwargs: Any):
        self.result_override = kwargs.pop("result_override")
        super().__init__(*args, **kwargs)

    async def get_root_value(self, request: ChannelsRequest):
        return Query()

    async def get_context(self, request: ChannelsRequest, response: TemporalResponse):
        context = await super().get_context(request, response)

        return get_context(context)

    async def process_result(
        self, request: ChannelsRequest, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        if self.result_override:
            return self.result_override(result)

        return await super().process_result(request, result)


class DebuggableSyncGraphQLHTTPConsumer(
    SyncGraphQLHTTPConsumer[dict[str, object], object]
):
    result_override: ResultOverrideFunction = None

    def __init__(self, *args: Any, **kwargs: Any):
        self.result_override = kwargs.pop("result_override")
        super().__init__(*args, **kwargs)

    def get_root_value(self, request: ChannelsRequest):
        return Query()

    def get_context(self, request: ChannelsRequest, response: TemporalResponse):
        context = super().get_context(request, response)

        return get_context(context)

    def process_result(
        self, request: ChannelsRequest, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        if self.result_override:
            return self.result_override(result)

        return super().process_result(request, result)


class DebuggableGraphQLWSConsumer(
    OnWSConnectMixin, GraphQLWSConsumer[dict[str, object], object]
):
    graphql_transport_ws_handler_class = DebuggableGraphQLTransportWSHandler
    graphql_ws_handler_class = DebuggableGraphQLWSHandler

    async def get_context(
        self, request: GraphQLWSConsumer, response: GraphQLWSConsumer
    ):
        context = await super().get_context(request, response)

        return get_context(context)


class ChannelsHttpClient(HttpClient):
    """A client to test websockets over channels."""

    def __init__(
        self,
        graphiql: Optional[bool] = None,
        graphql_ide: Optional[GraphQL_IDE] = "graphiql",
        allow_queries_via_get: bool = True,
        result_override: ResultOverrideFunction = None,
        multipart_uploads_enabled: bool = False,
    ):
        self.ws_app = DebuggableGraphQLWSConsumer.as_asgi(
            schema=schema,
            keep_alive=False,
        )

        self.http_app = DebuggableGraphQLHTTPConsumer.as_asgi(
            schema=schema,
            graphiql=graphiql,
            graphql_ide=graphql_ide,
            allow_queries_via_get=allow_queries_via_get,
            result_override=result_override,
            multipart_uploads_enabled=multipart_uploads_enabled,
        )

    def create_app(self, **kwargs: Any) -> None:
        self.ws_app = DebuggableGraphQLWSConsumer.as_asgi(schema=schema, **kwargs)

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

        headers = self._get_headers(method=method, headers=headers, files=files)

        if method == "post":
            if body and files:
                header_pairs, body = create_multipart_request_body(body, files)
                headers = dict(header_pairs)
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
        headers: Optional[dict[str, str]] = None,
        body: bytes = b"",
    ) -> Response:
        # HttpCommunicator expects tuples of bytestrings
        header_tuples = (
            [(k.encode(), v.encode()) for k, v in headers.items()] if headers else []
        )

        communicator = HttpCommunicator(
            self.http_app,
            method.upper(),
            url,
            body=body,
            headers=header_tuples,
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
        protocols: list[str],
    ) -> AsyncGenerator[WebSocketClient, None]:
        client = WebsocketCommunicator(self.ws_app, url, subprotocols=protocols)

        connected, subprotocol_or_close_code = await client.connect()
        assert connected

        try:
            yield ChannelsWebSocketClient(
                client, accepted_subprotocol=subprotocol_or_close_code
            )
        finally:
            await client.disconnect()


class SyncChannelsHttpClient(ChannelsHttpClient):
    def __init__(
        self,
        graphiql: Optional[bool] = None,
        graphql_ide: Optional[GraphQL_IDE] = "graphiql",
        allow_queries_via_get: bool = True,
        result_override: ResultOverrideFunction = None,
        multipart_uploads_enabled: bool = False,
    ):
        self.http_app = DebuggableSyncGraphQLHTTPConsumer.as_asgi(
            schema=schema,
            graphiql=graphiql,
            graphql_ide=graphql_ide,
            allow_queries_via_get=allow_queries_via_get,
            result_override=result_override,
            multipart_uploads_enabled=multipart_uploads_enabled,
        )


class ChannelsWebSocketClient(WebSocketClient):
    def __init__(
        self, client: WebsocketCommunicator, accepted_subprotocol: Optional[str]
    ):
        self.ws = client
        self._closed: bool = False
        self._close_code: Optional[int] = None
        self._close_reason: Optional[str] = None
        self._accepted_subprotocol = accepted_subprotocol

    def name(self) -> str:
        return "channels"

    async def send_text(self, payload: str) -> None:
        await self.ws.send_to(text_data=payload)

    async def send_json(self, payload: Mapping[str, object]) -> None:
        await self.ws.send_json_to(payload)

    async def send_bytes(self, payload: bytes) -> None:
        await self.ws.send_to(bytes_data=payload)

    async def receive(self, timeout: Optional[float] = None) -> Message:
        m = await self.ws.receive_output(timeout=timeout)  # type: ignore
        if m["type"] == "websocket.close":
            self._closed = True
            self._close_code = m["code"]
            self._close_reason = m.get("reason")
            return Message(type=m["type"], data=m["code"], extra=m.get("reason"))
        if m["type"] == "websocket.send":
            return Message(type=m["type"], data=m["text"])
        return Message(type=m["type"], data=m["data"], extra=m["extra"])

    async def receive_json(self, timeout: Optional[float] = None) -> Any:
        m = await self.ws.receive_output(timeout=timeout)  # type: ignore
        assert m["type"] == "websocket.send"
        assert "text" in m
        return json_module.loads(m["text"])

    async def close(self) -> None:
        await self.ws.disconnect()
        self._closed = True

    @property
    def accepted_subprotocol(self) -> Optional[str]:
        return self._accepted_subprotocol

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
