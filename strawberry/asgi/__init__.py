import asyncio
import json
import typing

from starlette import status
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState

from graphql import ExecutionResult as GraphQLExecutionResult, GraphQLError
from graphql.error import format_error as format_graphql_error

from strawberry.file_uploads.data import replace_placeholders_with_files
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
    GQL_ERROR,
    GQL_START,
    GQL_STOP,
)
from .utils import get_graphiql_html


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
        self,
        request: typing.Union[Request, WebSocket],
        response: typing.Optional[Response] = None,
    ) -> typing.Optional[typing.Any]:
        return {"request": request, "response": response}

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
                    try:
                        async_result = await self.start_subscription(
                            message.get("payload"), operation_id, websocket
                        )
                    except GraphQLError as error:
                        # Syntax errors can cause errors early on but bubble up before
                        # being converted to an `ExecutionResult` so we need to handle
                        # them here.
                        payload = format_graphql_error(error)
                        await self._send_message(
                            websocket, GQL_ERROR, payload, operation_id
                        )
                        continue

                    # Errors -- such as those caused by or an invalid subscription field
                    # being specified in the query -- can cause this to fail in a bad
                    # way. In addition to the stack trace in the server logs, to the
                    # client it appears as though the connection was severed for no
                    # reason.
                    if isinstance(async_result, GraphQLExecutionResult):
                        assert async_result.errors is not None
                        payload = format_graphql_error(async_result.errors[0])
                        await self._send_message(
                            websocket, GQL_ERROR, payload, operation_id
                        )
                        continue

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

    def get_graphiql_response(self) -> HTMLResponse:
        html = get_graphiql_html()

        return HTMLResponse(html)

    async def get_http_response(
        self,
        request: Request,
        execute: typing.Callable,
        process_result: typing.Callable,
        graphiql: bool,
        root_value: typing.Optional[typing.Any],
        context: typing.Optional[typing.Any],
    ) -> Response:
        if request.method == "GET":
            if not graphiql:
                return HTMLResponse(status_code=status.HTTP_404_NOT_FOUND)

            return self.get_graphiql_response()

        if request.method == "POST":
            content_type = request.headers.get("Content-Type", "")
            if "application/json" in content_type:
                data = await request.json()
            elif content_type.startswith("multipart/form-data"):
                multipart_data = await request.form()
                operations = json.loads(multipart_data.get("operations", "{}"))
                files_map = json.loads(multipart_data.get("map", "{}"))

                data = replace_placeholders_with_files(
                    operations, files_map, multipart_data
                )

            else:
                return PlainTextResponse(
                    "Unsupported Media Type",
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                )
        else:
            return PlainTextResponse(
                "Method Not Allowed",
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            )

        try:
            query = data["query"]
            variables = data.get("variables")
            operation_name = data.get("operationName")
        except KeyError:
            return PlainTextResponse(
                "No GraphQL query found in the request",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        result = await execute(
            query,
            variables=variables,
            context=context,
            operation_name=operation_name,
            root_value=root_value,
        )

        response_data = await process_result(request=request, result=result)

        return JSONResponse(response_data, status_code=status.HTTP_200_OK)

    async def handle_http(self, scope: Scope, receive: Receive, send: Send):
        request = Request(scope=scope, receive=receive)
        root_value = await self.get_root_value(request)

        sub_response = Response(
            content=None,
            status_code=None,  # type: ignore
            headers=None,
            media_type=None,
            background=None,
        )

        context = await self.get_context(request=request, response=sub_response)

        response = await self.get_http_response(
            request=request,
            execute=self.execute,
            process_result=self.process_result,
            graphiql=self.graphiql,
            root_value=root_value,
            context=context,
        )

        response.headers.raw.extend(sub_response.headers.raw)

        if sub_response.status_code:
            response.status_code = sub_response.status_code

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
