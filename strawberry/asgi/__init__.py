from datetime import timedelta
from typing import Any, Optional, Union

from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocket

from strawberry.asgi.handlers import (
    GraphQLTransportWSHandler,
    GraphQLWSHandler,
    HTTPHandler,
)
from strawberry.http import GraphQLHTTPResponse, process_result
from strawberry.schema import BaseSchema
from strawberry.subscriptions import GRAPHQL_TRANSPORT_PROTOCOL, GRAPHQL_WS_PROTOCOL
from strawberry.types import ExecutionResult


class GraphQL:
    graphql_transport_ws_handler_class = GraphQLTransportWSHandler
    graphql_ws_handler_class = GraphQLWSHandler
    http_handler_class = HTTPHandler

    def __init__(
        self,
        schema: BaseSchema,
        graphiql: bool = True,
        keep_alive: bool = False,
        keep_alive_interval: float = 1,
        debug: bool = False,
        protocols=(GRAPHQL_TRANSPORT_PROTOCOL, GRAPHQL_WS_PROTOCOL),
        connection_init_wait_timeout: timedelta = timedelta(minutes=1),
    ) -> None:
        self.schema = schema
        self.graphiql = graphiql
        self.keep_alive = keep_alive
        self.keep_alive_interval = keep_alive_interval
        self.debug = debug
        self.protocols = protocols
        self.connection_init_wait_timeout = connection_init_wait_timeout

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            await self.http_handler_class(
                schema=self.schema,
                graphiql=self.graphiql,
                debug=self.debug,
                get_context=self.get_context,
                get_root_value=self.get_root_value,
                process_result=self.process_result,
            ).handle(scope=scope, receive=receive, send=send)

        elif scope["type"] == "websocket":
            ws = WebSocket(scope=scope, receive=receive, send=send)
            intersecting_protocols = set(ws["subprotocols"]) & set(self.protocols)

            if GRAPHQL_TRANSPORT_PROTOCOL in intersecting_protocols:
                await self.graphql_transport_ws_handler_class(
                    schema=self.schema,
                    debug=self.debug,
                    connection_init_wait_timeout=self.connection_init_wait_timeout,
                    get_context=self.get_context,
                    get_root_value=self.get_root_value,
                    ws=ws,
                ).handle()
            elif GRAPHQL_WS_PROTOCOL in intersecting_protocols:
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
            raise ValueError("Unknown scope type: %r" % (scope["type"],))

    async def get_root_value(self, request: Union[Request, WebSocket]) -> Optional[Any]:
        return None

    async def get_context(
        self,
        request: Union[Request, WebSocket],
        response: Optional[Response] = None,
    ) -> Optional[Any]:
        return {"request": request, "response": response}

    async def process_result(
        self, request: Request, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        return process_result(result)
