import asyncio
import json
from abc import ABC, abstractmethod
from contextlib import suppress
from typing import Any, AsyncGenerator, Callable, Optional, Union, cast

from starlette import status
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState

from graphql import ExecutionResult as GraphQLExecutionResult, GraphQLError
from graphql.error import format_error as format_graphql_error

from strawberry.asgi.utils import get_graphiql_html
from strawberry.exceptions import MissingQueryError
from strawberry.file_uploads.utils import replace_placeholders_with_files
from strawberry.http import GraphQLHTTPResponse, parse_request_data, process_result
from strawberry.schema import BaseSchema
from strawberry.subscriptions.constants import (
    GQL_COMPLETE,
    GQL_CONNECTION_ACK,
    GQL_CONNECTION_INIT,
    GQL_CONNECTION_KEEP_ALIVE,
    GQL_CONNECTION_TERMINATE,
    GQL_DATA,
    GQL_ERROR,
    GQL_START,
    GQL_STOP,
    GRAPHQL_WS,
)
from strawberry.subscriptions.types import (
    OperationMessage,
    OperationMessagePayload,
    StartPayload,
)
from strawberry.types import ExecutionResult
from strawberry.utils.debug import pretty_print_graphql_operation


class BaseGraphQLApp(ABC):
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
        self.debug = debug

    @abstractmethod
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        pass  # pragma: no cover

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


class WebSocketHandler(BaseGraphQLApp, ABC):
    async def handle_websocket(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        ws = WebSocket(scope=scope, receive=receive, send=send)
        await ws.accept(subprotocol=GRAPHQL_WS)

        ws.state.subscriptions = {}
        ws.state.tasks = {}
        ws.state.keep_alive_task = None

        try:
            while ws.application_state != WebSocketState.DISCONNECTED:
                try:
                    message: OperationMessage = await ws.receive_json()
                except KeyError:
                    # Ignore non-text/json for consistency with the aiohttp impl. and
                    # to make this impl. more robust.
                    continue
                await self.handle_ws_message(ws, message)
        except WebSocketDisconnect:  # pragma: no cover
            pass
        finally:
            if ws.state.keep_alive_task:
                ws.state.keep_alive_task.cancel()
                with suppress(BaseException):
                    await ws.state.keep_alive_task

            for operation_id in list(ws.state.subscriptions.keys()):
                await self.cleanup_operation(ws, operation_id)

    async def handle_ws_message(self, ws: WebSocket, message: OperationMessage) -> None:
        message_type = message.get("type")

        if message_type == GQL_CONNECTION_INIT:
            await self.handle_connection_init(ws)
        elif message_type == GQL_CONNECTION_TERMINATE:
            await self.handle_connection_terminate(ws)
        elif message_type == GQL_START:
            await self.handle_start(ws, message)
        elif message_type == GQL_STOP:
            await self.handle_stop(ws, message)

    async def handle_connection_init(self, ws: WebSocket) -> None:
        await ws.send_json({"type": GQL_CONNECTION_ACK})

        if self.keep_alive:
            ws.state.keep_alive_task = asyncio.create_task(self.handle_keep_alive(ws))

    async def handle_connection_terminate(self, ws: WebSocket) -> None:
        await ws.close()

    async def handle_start(self, ws: WebSocket, message: OperationMessage) -> None:
        operation_id = message["id"]
        payload = cast(StartPayload, message["payload"])
        query = payload["query"]
        operation_name = payload.get("operationName")
        variables = payload.get("variables")
        context = await self.get_context(ws)
        root_value = await self.get_root_value(ws)

        if self.debug:
            pretty_print_graphql_operation(operation_name, query, variables)

        try:
            result_source = await self.schema.subscribe(
                query=query,
                variable_values=variables,
                operation_name=operation_name,
                context_value=context,
                root_value=root_value,
            )
        except GraphQLError as error:
            error_payload = format_graphql_error(error)
            await self.send_message(ws, GQL_ERROR, operation_id, error_payload)
            return

        if isinstance(result_source, GraphQLExecutionResult):
            assert result_source.errors
            error_payload = format_graphql_error(result_source.errors[0])
            await self.send_message(ws, GQL_ERROR, operation_id, error_payload)
            return

        ws.state.subscriptions[operation_id] = result_source
        ws.state.tasks[operation_id] = asyncio.create_task(
            self.handle_async_results(result_source, operation_id, ws)
        )

    async def handle_stop(self, ws: WebSocket, message: OperationMessage) -> None:
        operation_id = message["id"]
        await self.cleanup_operation(ws, operation_id)

    async def handle_keep_alive(self, ws: WebSocket) -> None:
        while ws.application_state != WebSocketState.DISCONNECTED:  # pragma: no cover
            await ws.send_json({"type": GQL_CONNECTION_KEEP_ALIVE})
            await asyncio.sleep(self.keep_alive_interval)

    async def handle_async_results(
        self, result_source: AsyncGenerator, operation_id: str, ws: WebSocket
    ) -> None:
        try:
            async for result in result_source:
                payload = {"data": result.data}
                if result.errors:
                    payload["errors"] = [
                        format_graphql_error(err) for err in result.errors
                    ]
                await self.send_message(ws, GQL_DATA, operation_id, payload)
        except asyncio.CancelledError:
            # CancelledErrors are expected during task cleanup.
            pass
        except Exception as error:
            # GraphQLErrors are handled by graphql-core and included in the
            # ExecutionResult
            error = GraphQLError(str(error), original_error=error)
            await self.send_message(
                ws,
                GQL_DATA,
                operation_id,
                {"data": None, "errors": [format_graphql_error(error)]},
            )

        await self.send_message(ws, GQL_COMPLETE, operation_id, None)

    @classmethod
    async def cleanup_operation(cls, ws: WebSocket, operation_id: str) -> None:
        await ws.state.subscriptions[operation_id].aclose()
        del ws.state.subscriptions[operation_id]

        ws.state.tasks[operation_id].cancel()
        with suppress(BaseException):
            await ws.state.tasks[operation_id]
        del ws.state.tasks[operation_id]

    @classmethod
    async def send_message(
        cls,
        ws: WebSocket,
        type_: str,
        operation_id: str,
        payload: Optional[OperationMessagePayload] = None,
    ) -> None:
        data: OperationMessage = {"type": type_, "id": operation_id}
        if payload:
            data["payload"] = payload
        await ws.send_json(data)


class HTTPHandler(BaseGraphQLApp, ABC):
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

    async def get_http_response(
        self,
        request: Request,
        execute: Callable,
        process_result: Callable,
        graphiql: bool,
        root_value: Optional[Any],
        context: Optional[Any],
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
            request_data = parse_request_data(data)
        except MissingQueryError:
            return PlainTextResponse(
                "No GraphQL query found in the request",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        result = await execute(
            request_data.query,
            variables=request_data.variables,
            context=context,
            operation_name=request_data.operation_name,
            root_value=root_value,
        )

        response_data = await process_result(request=request, result=result)

        return JSONResponse(response_data, status_code=status.HTTP_200_OK)

    def get_graphiql_response(self) -> HTMLResponse:
        html = get_graphiql_html()

        return HTMLResponse(html)

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


class GraphQL(HTTPHandler, WebSocketHandler, BaseGraphQLApp):
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            await self.handle_http(scope=scope, receive=receive, send=send)
        elif scope["type"] == "websocket":
            await self.handle_websocket(scope=scope, receive=receive, send=send)
        else:  # pragma: no cover
            raise ValueError("Unknown scope type: %r" % (scope["type"],))
