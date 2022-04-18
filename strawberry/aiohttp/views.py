import asyncio
from datetime import timedelta

from aiohttp import web
from strawberry.aiohttp.handlers import (
    GraphQLTransportWSHandler,
    GraphQLWSHandler,
    HTTPHandler,
)
from strawberry.http import GraphQLHTTPResponse, process_result
from strawberry.schema import BaseSchema
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL
from strawberry.types import ExecutionResult


class GraphQLView:
    # Mark the view as coroutine so that AIOHTTP does not confuse it with a deprecated
    # bare handler function.
    _is_coroutine = asyncio.coroutines._is_coroutine  # type: ignore[attr-defined]

    graphql_transport_ws_handler_class = GraphQLTransportWSHandler
    graphql_ws_handler_class = GraphQLWSHandler
    http_handler_class = HTTPHandler

    def __init__(
        self,
        schema: BaseSchema,
        graphiql: bool = True,
        allow_queries_via_get: bool = True,
        keep_alive: bool = True,
        keep_alive_interval: float = 1,
        debug: bool = False,
        subscription_protocols=(GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL),
        connection_init_wait_timeout: timedelta = timedelta(minutes=1),
    ):
        self.schema = schema
        self.graphiql = graphiql
        self.allow_queries_via_get = allow_queries_via_get
        self.keep_alive = keep_alive
        self.keep_alive_interval = keep_alive_interval
        self.debug = debug
        self.subscription_protocols = subscription_protocols
        self.connection_init_wait_timeout = connection_init_wait_timeout

    async def __call__(self, request: web.Request) -> web.StreamResponse:
        ws = web.WebSocketResponse(protocols=self.subscription_protocols)
        ws_test = ws.can_prepare(request)

        if ws_test.ok:
            if ws_test.protocol == GRAPHQL_TRANSPORT_WS_PROTOCOL:
                return await self.graphql_transport_ws_handler_class(
                    schema=self.schema,
                    debug=self.debug,
                    connection_init_wait_timeout=self.connection_init_wait_timeout,
                    get_context=self.get_context,
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
        else:
            return await self.http_handler_class(
                schema=self.schema,
                graphiql=self.graphiql,
                allow_queries_via_get=self.allow_queries_via_get,
                get_context=self.get_context,
                get_root_value=self.get_root_value,
                process_result=self.process_result,
                request=request,
            ).handle()

    async def get_root_value(self, request: web.Request) -> object:
        return None

    async def get_context(
        self, request: web.Request, response: web.StreamResponse
    ) -> object:
        return {"request": request, "response": response}

    async def process_result(
        self, request: web.Request, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        return process_result(result)
