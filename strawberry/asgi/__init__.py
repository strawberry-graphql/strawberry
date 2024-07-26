from __future__ import annotations

import warnings
from datetime import timedelta
from typing import (
    TYPE_CHECKING,
    Any,
    Mapping,
    Optional,
    Sequence,
    Union,
    cast,
)

from starlette import status
from starlette.requests import Request
from starlette.responses import HTMLResponse, PlainTextResponse, Response
from starlette.websockets import WebSocket

from strawberry.asgi.handlers import (
    GraphQLTransportWSHandler,
    GraphQLWSHandler,
)
from strawberry.http.async_base_view import AsyncBaseHTTPView, AsyncHTTPRequestAdapter
from strawberry.http.exceptions import HTTPException
from strawberry.http.types import FormData, HTTPMethod, QueryParams
from strawberry.http.typevars import (
    Context,
    RootValue,
)
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL

if TYPE_CHECKING:
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
        return cast(HTTPMethod, self.request.method.upper())

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


class GraphQL(
    AsyncBaseHTTPView[
        Union[Request, WebSocket],
        Response,
        Response,
        Context,
        RootValue,
    ]
):
    graphql_transport_ws_handler_class = GraphQLTransportWSHandler
    graphql_ws_handler_class = GraphQLWSHandler
    allow_queries_via_get = True
    request_adapter_class = ASGIRequestAdapter  # pyright: ignore

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
    ) -> None:
        self.schema = schema
        self.allow_queries_via_get = allow_queries_via_get
        self.keep_alive = keep_alive
        self.keep_alive_interval = keep_alive_interval
        self.debug = debug
        self.protocols = subscription_protocols
        self.connection_init_wait_timeout = connection_init_wait_timeout

        if graphiql is not None:
            warnings.warn(
                "The `graphiql` argument is deprecated in favor of `graphql_ide`",
                DeprecationWarning,
                stacklevel=2,
            )
            self.graphql_ide = "graphiql" if graphiql else None
        else:
            self.graphql_ide = graphql_ide

    async def __call__(self, scope: Request, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            return await self.handle_http(scope, receive, send)  # type: ignore

        elif scope["type"] == "websocket":
            ws = WebSocket(scope, receive=receive, send=send)  # type: ignore
            preferred_protocol = self.pick_preferred_protocol(ws)

            if preferred_protocol == GRAPHQL_TRANSPORT_WS_PROTOCOL:
                await self.graphql_transport_ws_handler_class(
                    schema=self.schema,
                    debug=self.debug,
                    connection_init_wait_timeout=self.connection_init_wait_timeout,
                    get_context=self.get_context,
                    get_root_value=self.get_root_value,
                    ws=ws,
                ).handle()

            elif preferred_protocol == GRAPHQL_WS_PROTOCOL:
                await self.graphql_ws_handler_class(
                    schema=self.schema,
                    debug=self.debug,
                    keep_alive=self.keep_alive,
                    keep_alive_interval=self.keep_alive_interval,
                    get_context=self.get_context,
                    get_root_value=self.get_root_value,
                    ws=ws,
                ).handle()

            else:
                # Subprotocol not acceptable
                await ws.close(code=4406)

        else:  # pragma: no cover
            raise ValueError("Unknown scope type: {!r}".format(scope["type"]))

    def pick_preferred_protocol(self, ws: WebSocket) -> Optional[str]:
        protocols = ws["subprotocols"]
        intersection = set(protocols) & set(self.protocols)
        sorted_intersection = sorted(intersection, key=protocols.index)
        return next(iter(sorted_intersection), None)

    async def get_root_value(self, request: Union[Request, WebSocket]) -> Optional[Any]:
        return None

    async def get_context(
        self, request: Union[Request, WebSocket], response: Response
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

    async def handle_http(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        request = Request(scope=scope, receive=receive)

        try:
            response = await self.run(request)
        except HTTPException as e:
            response = PlainTextResponse(e.reason, status_code=e.status_code)  # pyright: ignore

        await response(scope, receive, send)

    async def render_graphql_ide(self, request: Union[Request, WebSocket]) -> Response:
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
