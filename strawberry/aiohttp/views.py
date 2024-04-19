from __future__ import annotations

import asyncio
import warnings
from datetime import timedelta
from io import BytesIO
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    Mapping,
    Optional,
    cast,
)

from aiohttp import web
from strawberry.aiohttp.handlers import (
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
    from strawberry.http import GraphQLHTTPResponse
    from strawberry.http.ides import GraphQL_IDE
    from strawberry.schema import BaseSchema


class AioHTTPRequestAdapter(AsyncHTTPRequestAdapter):
    def __init__(self, request: web.Request) -> None:
        self.request = request

    @property
    def query_params(self) -> QueryParams:
        return self.request.query.copy()  # type: ignore[attr-defined]

    async def get_body(self) -> str:
        return (await self.request.content.read()).decode()

    @property
    def method(self) -> HTTPMethod:
        return cast(HTTPMethod, self.request.method.upper())

    @property
    def headers(self) -> Mapping[str, str]:
        return self.request.headers

    async def get_form_data(self) -> FormData:
        reader = await self.request.multipart()

        data: Dict[str, Any] = {}
        files: Dict[str, Any] = {}

        async for field in reader:
            assert field.name

            if field.filename:
                files[field.name] = BytesIO(await field.read(decode=False))
            else:
                data[field.name] = await field.text()

        return FormData(files=files, form=data)

    @property
    def content_type(self) -> Optional[str]:
        return self.request.content_type


class GraphQLView(
    AsyncBaseHTTPView[web.Request, web.Response, web.Response, Context, RootValue]
):
    # Mark the view as coroutine so that AIOHTTP does not confuse it with a deprecated
    # bare handler function.
    _is_coroutine = asyncio.coroutines._is_coroutine  # type: ignore[attr-defined]

    graphql_transport_ws_handler_class = GraphQLTransportWSHandler
    graphql_ws_handler_class = GraphQLWSHandler
    allow_queries_via_get = True
    request_adapter_class = AioHTTPRequestAdapter

    def __init__(
        self,
        schema: BaseSchema,
        graphiql: Optional[bool] = None,
        graphql_ide: Optional[GraphQL_IDE] = "graphiql",
        allow_queries_via_get: bool = True,
        keep_alive: bool = True,
        keep_alive_interval: float = 1,
        debug: bool = False,
        subscription_protocols: Iterable[str] = (
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
        self.subscription_protocols = subscription_protocols
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

    async def render_graphql_ide(self, request: web.Request) -> web.Response:
        return web.Response(text=self.graphql_ide_html, content_type="text/html")

    async def get_sub_response(self, request: web.Request) -> web.Response:
        return web.Response()

    async def __call__(self, request: web.Request) -> web.StreamResponse:
        ws = web.WebSocketResponse(protocols=self.subscription_protocols)
        ws_test = ws.can_prepare(request)

        if not ws_test.ok:
            try:
                return await self.run(request=request)
            except HTTPException as e:
                return web.Response(
                    body=e.reason,
                    status=e.status_code,
                )

        if ws_test.protocol == GRAPHQL_TRANSPORT_WS_PROTOCOL:
            return await self.graphql_transport_ws_handler_class(
                schema=self.schema,
                debug=self.debug,
                connection_init_wait_timeout=self.connection_init_wait_timeout,
                get_context=self.get_context,  # type: ignore
                get_root_value=self.get_root_value,
                request=request,
            ).handle()
        elif ws_test.protocol == GRAPHQL_WS_PROTOCOL:
            return await self.graphql_ws_handler_class(
                schema=self.schema,
                debug=self.debug,
                keep_alive=self.keep_alive,
                keep_alive_interval=self.keep_alive_interval,
                get_context=self.get_context,
                get_root_value=self.get_root_value,
                request=request,
            ).handle()
        else:
            await ws.prepare(request)
            await ws.close(code=4406, message=b"Subprotocol not acceptable")
            return ws

    async def get_root_value(self, request: web.Request) -> Optional[RootValue]:
        return None

    async def get_context(
        self, request: web.Request, response: web.Response
    ) -> Context:
        return {"request": request, "response": response}  # type: ignore

    def create_response(
        self, response_data: GraphQLHTTPResponse, sub_response: web.Response
    ) -> web.Response:
        sub_response.text = self.encode_json(response_data)
        sub_response.content_type = "application/json"

        return sub_response
