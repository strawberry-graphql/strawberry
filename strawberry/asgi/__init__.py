import asyncio
import typing

from starlette.requests import Request
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState

from graphql import GraphQLError
from graphql.error import format_error as format_graphql_error

from strawberry.http import GraphQLHTTPResponse, process_result
from strawberry.types import ExecutionResult

from ..schema import BaseSchema
from ..utils.debug import pretty_print_graphql_operation
from .constants import (
    GQL_COMPLETE,
    GQL_CONNECTION_ACK,
    GQL_CONNECTION_INIT,
    GQL_CONNECTION_KEEP_ALIVE,
    GQL_CONNECTION_TERMINATE,
    GQL_DATA,
    GQL_START,
    GQL_STOP,
)
from .http import get_http_response


class GraphQL:
    def __init__(
        self,
        schema: BaseSchema,
        graphiql: bool = True,
        keep_alive: bool = False,
        keep_alive_interval: float = 1,
        debug: bool = False,
    ) -> None:
        self.schema = schema
        self.graphiql = graphiql
        self.keep_alive = keep_alive
        self.keep_alive_interval = keep_alive_interval
        self._keep_alive_task: typing.Optional[asyncio.Task[typing.Any]] = None
        self.debug = debug

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            await self.handle_http(scope=scope, receive=receive, send=send)
        elif scope["type"] == "websocket":
            await self.handle_websocket(scope=scope, receive=receive, send=send)
        else:  # pragma: no cover
            raise ValueError("Unknown scope type: %r" % (scope["type"],))

    async def get_root_value(self, request: Request) -> typing.Optional[typing.Any]:
        return None

    async def get_context(
        self, request: typing.Union[Request, WebSocket]
    ) -> typing.Optional[typing.Any]:
        return {"request": request}

    async def handle_keep_alive(self, websocket):
        if (
            websocket.application_state == WebSocketState.DISCONNECTED
        ):  # pragma: no cover
            return

        await asyncio.sleep(self.keep_alive_interval)
        await websocket.send_json({"type": GQL_CONNECTION_KEEP_ALIVE})

        self._keep_alive_task = asyncio.create_task(self.handle_keep_alive(websocket))

    async def handle_websocket(self, scope: Scope, receive: Receive, send: Send):
        websocket = WebSocket(scope=scope, receive=receive, send=send)

        subscriptions: typing.Dict[str, typing.AsyncGenerator] = {}
        tasks = {}

        await websocket.accept(subprotocol="graphql-ws")

        try:
            while (
                websocket.client_state != WebSocketState.DISCONNECTED
                and websocket.application_state != WebSocketState.DISCONNECTED
            ):
                message = await websocket.receive_json()

                operation_id = message.get("id")
                message_type = message.get("type")

                if message_type == GQL_CONNECTION_INIT:
                    await websocket.send_json({"type": GQL_CONNECTION_ACK})

                    if self.keep_alive:
                        self._keep_alive_task = asyncio.create_task(
                            self.handle_keep_alive(websocket)
                        )
                elif message_type == GQL_CONNECTION_TERMINATE:
                    await websocket.close()
                elif message_type == GQL_START:
                    async_result = await self.start_subscription(
                        message.get("payload"), operation_id, websocket
                    )

                    subscriptions[operation_id] = async_result

                    tasks[operation_id] = asyncio.create_task(
                        self.handle_async_results(async_result, operation_id, websocket)
                    )
                elif message_type == GQL_STOP:  # pragma: no cover
                    if operation_id not in subscriptions:
                        return

                    await subscriptions[operation_id].aclose()
                    tasks[operation_id].cancel()
                    del tasks[operation_id]
                    del subscriptions[operation_id]
        except WebSocketDisconnect:  # pragma: no cover
            pass
        finally:
            if self._keep_alive_task:
                self._keep_alive_task.cancel()

            for operation_id in subscriptions:
                await subscriptions[operation_id].aclose()
                tasks[operation_id].cancel()

    async def start_subscription(self, data, operation_id: str, websocket: WebSocket):
        query = data["query"]
        variables = data.get("variables")
        operation_name = data.get("operation_name")

        if self.debug:
            pretty_print_graphql_operation(operation_name, query, variables)

        context = await self.get_context(websocket)

        return await self.schema.subscribe(
            query,
            variable_values=variables,
            operation_name=operation_name,
            context_value=context,
        )

    async def handle_async_results(
        self, results: typing.AsyncGenerator, operation_id: str, websocket: WebSocket
    ):
        try:
            async for result in results:
                payload = {"data": result.data}

                if result.errors:
                    payload["errors"] = [
                        format_graphql_error(err) for err in result.errors
                    ]

                await self._send_message(websocket, GQL_DATA, payload, operation_id)
        except Exception as error:
            if not isinstance(error, GraphQLError):
                error = GraphQLError(str(error), original_error=error)

            await self._send_message(
                websocket,
                GQL_DATA,
                {"data": None, "errors": [format_graphql_error(error)]},
                operation_id,
            )

        if (
            websocket.client_state != WebSocketState.DISCONNECTED
            and websocket.application_state != WebSocketState.DISCONNECTED
        ):
            await self._send_message(websocket, GQL_COMPLETE, None, operation_id)

    async def _send_message(
        self,
        websocket: WebSocket,
        type_: str,
        payload: typing.Any = None,
        operation_id: str = None,
    ) -> None:
        data = {"type": type_}

        if operation_id is not None:
            data["id"] = operation_id

        if payload is not None:
            data["payload"] = payload

        return await websocket.send_json(data)

    async def handle_http(self, scope: Scope, receive: Receive, send: Send):
        request = Request(scope=scope, receive=receive)
        root_value = await self.get_root_value(request)
        context = await self.get_context(request)

        response = await get_http_response(
            request=request,
            execute=self.execute,
            process_result=self.process_result,
            graphiql=self.graphiql,
            root_value=root_value,
            context=context,
        )

        await response(scope, receive, send)

    async def process_result(
        self, request: Request, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        return process_result(result)

    async def execute(
        self, query, variables=None, context=None, operation_name=None, root_value=None
    ):
        if self.debug:
            pretty_print_graphql_operation(operation_name, query, variables)

        return await self.schema.execute(
            query,
            root_value=root_value,
            variable_values=variables,
            operation_name=operation_name,
            context_value=context,
        )
