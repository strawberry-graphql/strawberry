from __future__ import annotations

import asyncio
import warnings
from datetime import timedelta
from io import BytesIO
from json.decoder import JSONDecodeError
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Optional,
    Union,
    cast,
)
from typing_extensions import TypeGuard

from aiohttp import ClientConnectionResetError, http, web
from aiohttp.multipart import BodyPartReader
from strawberry.http.async_base_view import (
    AsyncBaseHTTPView,
    AsyncHTTPRequestAdapter,
    AsyncWebSocketAdapter,
)
from strawberry.http.exceptions import (
    HTTPException,
    NonJsonMessageReceived,
    NonTextMessageReceived,
    WebSocketDisconnected,
)
from strawberry.http.types import FormData, HTTPMethod, QueryParams
from strawberry.http.typevars import (
    Context,
    RootValue,
)
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Mapping, Sequence

    from strawberry.http import GraphQLHTTPResponse
    from strawberry.http.ides import GraphQL_IDE
    from strawberry.schema import BaseSchema


class AiohttpHTTPRequestAdapter(AsyncHTTPRequestAdapter):
    def __init__(self, request: web.Request) -> None:
        self.request = request

    @property
    def query_params(self) -> QueryParams:
        return self.request.query.copy()  # type: ignore[attr-defined]

    async def get_body(self) -> str:
        return (await self.request.content.read()).decode()

    @property
    def method(self) -> HTTPMethod:
        return cast("HTTPMethod", self.request.method.upper())

    @property
    def headers(self) -> Mapping[str, str]:
        return self.request.headers

    async def get_form_data(self) -> FormData:
        reader = await self.request.multipart()

        data: dict[str, Any] = {}
        files: dict[str, Any] = {}

        while field := await reader.next():
            assert isinstance(field, BodyPartReader)
            assert field.name

            if field.filename:
                files[field.name] = BytesIO(await field.read(decode=False))
            else:
                data[field.name] = await field.text()

        return FormData(files=files, form=data)

    @property
    def content_type(self) -> Optional[str]:
        return self.headers.get("content-type")


class AiohttpWebSocketAdapter(AsyncWebSocketAdapter):
    def __init__(
        self, view: AsyncBaseHTTPView, request: web.Request, ws: web.WebSocketResponse
    ) -> None:
        super().__init__(view)
        self.request = request
        self.ws = ws

    async def iter_json(
        self, *, ignore_parsing_errors: bool = False
    ) -> AsyncGenerator[object, None]:
        async for ws_message in self.ws:
            if ws_message.type == http.WSMsgType.TEXT:
                try:
                    yield self.view.decode_json(ws_message.data)
                except JSONDecodeError as e:
                    if not ignore_parsing_errors:
                        raise NonJsonMessageReceived from e

            elif ws_message.type == http.WSMsgType.BINARY:
                raise NonTextMessageReceived

    async def send_json(self, message: Mapping[str, object]) -> None:
        try:
            await self.ws.send_str(self.view.encode_json(message))
        except (RuntimeError, ClientConnectionResetError) as exc:
            raise WebSocketDisconnected from exc

    async def close(self, code: int, reason: str) -> None:
        await self.ws.close(code=code, message=reason.encode())


class GraphQLView(
    AsyncBaseHTTPView[
        web.Request,
        Union[web.Response, web.StreamResponse],
        web.Response,
        web.Request,
        web.WebSocketResponse,
        Context,
        RootValue,
    ]
):
    # Mark the view as coroutine so that AIOHTTP does not confuse it with a deprecated
    # bare handler function.
    _is_coroutine = asyncio.coroutines._is_coroutine  # type: ignore[attr-defined]

    allow_queries_via_get = True
    request_adapter_class = AiohttpHTTPRequestAdapter
    websocket_adapter_class = AiohttpWebSocketAdapter

    def __init__(
        self,
        schema: BaseSchema,
        graphiql: Optional[bool] = None,
        graphql_ide: Optional[GraphQL_IDE] = "graphiql",
        allow_queries_via_get: bool = True,
        keep_alive: bool = True,
        keep_alive_interval: float = 1,
        debug: bool = False,
        subscription_protocols: Sequence[str] = (
            GRAPHQL_TRANSPORT_WS_PROTOCOL,
            GRAPHQL_WS_PROTOCOL,
        ),
        connection_init_wait_timeout: timedelta = timedelta(minutes=1),
        multipart_uploads_enabled: bool = False,
    ) -> None:
        self.schema = schema
        self.allow_queries_via_get = allow_queries_via_get
        self.keep_alive = keep_alive
        self.keep_alive_interval = keep_alive_interval
        self.debug = debug
        self.subscription_protocols = subscription_protocols
        self.connection_init_wait_timeout = connection_init_wait_timeout
        self.multipart_uploads_enabled = multipart_uploads_enabled

        if graphiql is not None:
            warnings.warn(
                "The `graphiql` argument is deprecated in favor of `graphql_ide`",
                DeprecationWarning,
                stacklevel=2,
            )
            self.graphql_ide = "graphiql" if graphiql else None
        else:
            self.graphql_ide = graphql_ide

    async def render_graphql_ide(self, request: web.Request) -> web.Response:
        return web.Response(text=self.graphql_ide_html, content_type="text/html")

    async def get_sub_response(self, request: web.Request) -> web.Response:
        return web.Response()

    def is_websocket_request(self, request: web.Request) -> TypeGuard[web.Request]:
        ws = web.WebSocketResponse(protocols=self.subscription_protocols)
        return ws.can_prepare(request).ok

    async def pick_websocket_subprotocol(self, request: web.Request) -> Optional[str]:
        ws = web.WebSocketResponse(protocols=self.subscription_protocols)
        return ws.can_prepare(request).protocol

    async def create_websocket_response(
        self, request: web.Request, subprotocol: Optional[str]
    ) -> web.WebSocketResponse:
        protocols = [subprotocol] if subprotocol else []
        ws = web.WebSocketResponse(protocols=protocols)
        await ws.prepare(request)
        return ws

    async def __call__(self, request: web.Request) -> web.StreamResponse:
        try:
            return await self.run(request=request)
        except HTTPException as e:
            return web.Response(
                body=e.reason,
                status=e.status_code,
            )

    async def get_root_value(self, request: web.Request) -> Optional[RootValue]:
        return None

    async def get_context(
        self, request: web.Request, response: Union[web.Response, web.WebSocketResponse]
    ) -> Context:
        return {"request": request, "response": response}  # type: ignore

    def create_response(
        self, response_data: GraphQLHTTPResponse, sub_response: web.Response
    ) -> web.Response:
        sub_response.text = self.encode_json(response_data)
        sub_response.content_type = "application/json"

        return sub_response

    async def create_streaming_response(
        self,
        request: web.Request,
        stream: Callable[[], AsyncGenerator[str, None]],
        sub_response: web.Response,
        headers: dict[str, str],
    ) -> web.StreamResponse:
        response = web.StreamResponse(
            status=sub_response.status,
            headers={
                **sub_response.headers,
                **headers,
            },
        )

        await response.prepare(request)

        async for data in stream():
            await response.write(data.encode())

        await response.write_eof()

        return response


__all__ = ["GraphQLView"]
