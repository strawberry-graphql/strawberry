from __future__ import annotations

import warnings
from datetime import timedelta
from json import JSONDecodeError
from typing import (
    TYPE_CHECKING,
    Callable,
    Optional,
    Union,
    cast,
)
from typing_extensions import TypeGuard

from starlette import status
from starlette.requests import Request
from starlette.responses import (
    HTMLResponse,
    PlainTextResponse,
    Response,
    StreamingResponse,
)
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState

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
    from collections.abc import AsyncGenerator, AsyncIterator, Mapping, Sequence

    from starlette.types import Receive, Scope, Send

    from strawberry.http import GraphQLHTTPResponse
    from strawberry.http.ides import GraphQL_IDE
    from strawberry.schema import BaseSchema


class ASGIRequestAdapter(AsyncHTTPRequestAdapter):
    def __init__(self, request: Request) -> None:
        self.request = request

    @property
    def query_params(self) -> QueryParams:
        return self.request.query_params

    @property
    def method(self) -> HTTPMethod:
        return cast("HTTPMethod", self.request.method.upper())

    @property
    def headers(self) -> Mapping[str, str]:
        return self.request.headers

    @property
    def content_type(self) -> Optional[str]:
        return self.request.headers.get("content-type")

    async def get_body(self) -> bytes:
        return await self.request.body()

    async def get_form_data(self) -> FormData:
        multipart_data = await self.request.form()

        return FormData(
            files=multipart_data,
            form=multipart_data,
        )


class ASGIWebSocketAdapter(AsyncWebSocketAdapter):
    def __init__(
        self, view: AsyncBaseHTTPView, request: WebSocket, response: WebSocket
    ) -> None:
        super().__init__(view)
        self.ws = response

    async def iter_json(
        self, *, ignore_parsing_errors: bool = False
    ) -> AsyncGenerator[object, None]:
        try:
            while self.ws.application_state != WebSocketState.DISCONNECTED:
                try:
                    text = await self.ws.receive_text()
                    yield self.view.decode_json(text)
                except JSONDecodeError as e:  # noqa: PERF203
                    if not ignore_parsing_errors:
                        raise NonJsonMessageReceived from e
        except KeyError as e:
            raise NonTextMessageReceived from e
        except WebSocketDisconnect:  # pragma: no cover
            pass

    async def send_json(self, message: Mapping[str, object]) -> None:
        try:
            await self.ws.send_text(self.view.encode_json(message))
        except WebSocketDisconnect as exc:
            raise WebSocketDisconnected from exc

    async def close(self, code: int, reason: str) -> None:
        await self.ws.close(code=code, reason=reason)


class GraphQL(
    AsyncBaseHTTPView[
        Request,
        Response,
        Response,
        WebSocket,
        WebSocket,
        Context,
        RootValue,
    ]
):
    allow_queries_via_get = True
    request_adapter_class = ASGIRequestAdapter
    websocket_adapter_class = ASGIWebSocketAdapter

    def __init__(
        self,
        schema: BaseSchema,
        graphiql: Optional[bool] = None,
        graphql_ide: Optional[GraphQL_IDE] = "graphiql",
        allow_queries_via_get: bool = True,
        keep_alive: bool = False,
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
        self.protocols = subscription_protocols
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

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            http_request = Request(scope=scope, receive=receive)

            try:
                response = await self.run(http_request)
            except HTTPException as e:
                response = PlainTextResponse(e.reason, status_code=e.status_code)

            await response(scope, receive, send)
        elif scope["type"] == "websocket":
            ws_request = WebSocket(scope, receive=receive, send=send)
            await self.run(ws_request)
        else:  # pragma: no cover
            raise ValueError("Unknown scope type: {!r}".format(scope["type"]))

    async def get_root_value(
        self, request: Union[Request, WebSocket]
    ) -> Optional[RootValue]:
        return None

    async def get_context(
        self, request: Union[Request, WebSocket], response: Union[Response, WebSocket]
    ) -> Context:
        return {"request": request, "response": response}  # type: ignore

    async def get_sub_response(
        self,
        request: Union[Request, WebSocket],
    ) -> Response:
        sub_response = Response()
        sub_response.status_code = None  # type: ignore
        del sub_response.headers["content-length"]

        return sub_response

    async def render_graphql_ide(self, request: Request) -> Response:
        return HTMLResponse(self.graphql_ide_html)

    def create_response(
        self, response_data: GraphQLHTTPResponse, sub_response: Response
    ) -> Response:
        response = Response(
            self.encode_json(response_data),
            status_code=status.HTTP_200_OK,
            media_type="application/json",
        )

        response.headers.raw.extend(sub_response.headers.raw)

        if sub_response.background:
            response.background = sub_response.background

        if sub_response.status_code:
            response.status_code = sub_response.status_code

        return response

    async def create_streaming_response(
        self,
        request: Request | WebSocket,
        stream: Callable[[], AsyncIterator[str]],
        sub_response: Response,
        headers: dict[str, str],
    ) -> Response:
        return StreamingResponse(
            stream(),
            status_code=sub_response.status_code or status.HTTP_200_OK,
            headers={
                **sub_response.headers,
                **headers,
            },
        )

    def is_websocket_request(
        self, request: Union[Request, WebSocket]
    ) -> TypeGuard[WebSocket]:
        return request.scope["type"] == "websocket"

    async def pick_websocket_subprotocol(self, request: WebSocket) -> Optional[str]:
        protocols = request["subprotocols"]
        intersection = set(protocols) & set(self.protocols)
        sorted_intersection = sorted(intersection, key=protocols.index)
        return next(iter(sorted_intersection), None)

    async def create_websocket_response(
        self, request: WebSocket, subprotocol: Optional[str]
    ) -> WebSocket:
        await request.accept(subprotocol=subprotocol)
        return request
