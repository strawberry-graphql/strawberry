import asyncio
import json
from abc import ABC, abstractmethod
from contextlib import suppress
from io import BytesIO
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Optional

from graphql import ExecutionResult as GraphQLExecutionResult, GraphQLError
from graphql.error import format_error as format_graphql_error

from aiohttp import http, web
from strawberry.exceptions import MissingQueryError
from strawberry.file_uploads.data import replace_placeholders_with_files
from strawberry.http import (
    GraphQLHTTPResponse,
    GraphQLRequestData,
    parse_request_data,
    process_result,
)
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
from strawberry.types import ExecutionResult


class BaseGraphQLView(ABC):
    def __init__(
        self,
        schema: BaseSchema,
        graphiql: bool = True,
        keep_alive: bool = True,
        keep_alive_interval: float = 1,
    ):
        self.schema = schema
        self.graphiql = graphiql
        self.keep_alive = keep_alive
        self.keep_alive_interval = keep_alive_interval

    @abstractmethod
    async def __call__(self, request: web.Request) -> web.StreamResponse:
        pass  # pragma: no cover

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


class WebSocketHandler(BaseGraphQLView, ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subscriptions: Dict[str, AsyncGenerator] = {}
        self.tasks: Dict[str, asyncio.Task] = {}
        self.keep_alive_task: Optional[asyncio.Task] = None

    async def handle_web_socket(self, request: web.Request) -> web.StreamResponse:
        ws = web.WebSocketResponse(protocols=[GRAPHQL_WS])
        await ws.prepare(request)

        try:
            async for message in ws:
                await self.handle_ws_message(request, ws, message)  # type: ignore
        finally:
            if self.keep_alive_task:
                self.keep_alive_task.cancel()
                with suppress(Exception):
                    await self.keep_alive_task

            for operation_id in list(self.subscriptions.keys()):
                await self.cleanup_operation(operation_id)

        return ws

    async def handle_ws_message(
        self,
        request: web.Request,
        ws: web.WebSocketResponse,
        ws_message: http.WSMessage,
    ) -> None:
        if ws_message.type == http.WSMsgType.TEXT:
            await self.handle_ws_text_message(request, ws, ws_message)

    async def handle_ws_text_message(
        self,
        request: web.Request,
        ws: web.WebSocketResponse,
        ws_text_message: http.WSMessage,
    ) -> None:
        message: dict = ws_text_message.json()
        message_type: str = message["type"]

        if message_type == GQL_CONNECTION_INIT:
            await self.handle_connection_init(ws)
        elif message_type == GQL_CONNECTION_TERMINATE:
            await self.handle_connection_terminate(ws)
        elif message_type == GQL_START:
            await self.handle_start(request, ws, message)
        elif message_type == GQL_STOP:
            await self.handle_stop(message)

    async def handle_connection_init(self, ws: web.WebSocketResponse) -> None:
        await ws.send_json({"type": GQL_CONNECTION_ACK})

        if self.keep_alive:
            self.keep_alive_task = asyncio.create_task(self.handle_keep_alive(ws))

    async def handle_connection_terminate(self, ws: web.WebSocketResponse) -> None:
        await ws.close()

    async def handle_start(
        self, request: web.Request, ws: web.WebSocketResponse, message: dict
    ) -> None:
        operation_id = message["id"]
        payload: dict = message["payload"]
        query = payload["query"]
        operation_name = payload.get("operation_name")
        variables = payload.get("variables")
        context = await self.get_context(request, ws)
        root_value = await self.get_root_value(request)

        try:
            result_source = await self.schema.subscribe(
                query,
                variable_values=variables,
                operation_name=operation_name,
                context_value=context,
                root_value=root_value,
            )
        except GraphQLError as error:
            payload = format_graphql_error(error)
            await self.send_message(ws, GQL_ERROR, operation_id, payload)
            return

        if isinstance(result_source, GraphQLExecutionResult):
            assert result_source.errors
            payload = format_graphql_error(result_source.errors[0])
            await self.send_message(ws, GQL_ERROR, operation_id, payload)
            return

        self.subscriptions[operation_id] = result_source
        self.tasks[operation_id] = asyncio.create_task(
            self.handle_async_results(result_source, operation_id, ws)
        )

    async def handle_stop(self, message: dict) -> None:
        operation_id = message["id"]
        await self.cleanup_operation(operation_id)

    async def handle_keep_alive(self, ws: web.WebSocketResponse) -> None:
        while True:
            await asyncio.sleep(self.keep_alive_interval)
            await ws.send_json({"type": GQL_CONNECTION_KEEP_ALIVE})

    async def handle_async_results(
        self,
        result_generator: AsyncGenerator,
        operation_id: str,
        ws: web.WebSocketResponse,
    ) -> None:
        try:
            async for result in result_generator:
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

    async def cleanup_operation(self, operation_id: str) -> None:
        await self.subscriptions[operation_id].aclose()
        del self.subscriptions[operation_id]

        self.tasks[operation_id].cancel()
        with suppress(Exception):
            await self.tasks[operation_id]
        del self.tasks[operation_id]

    @classmethod
    async def send_message(
        cls,
        ws: web.WebSocketResponse,
        type_: str,
        operation_id: str,
        payload: Optional[dict] = None,
    ) -> None:
        data: Dict[Any, Any] = {"type": type_, "id": operation_id}
        if payload is not None:
            data["payload"] = payload
        return await ws.send_json(data)

    @classmethod
    def is_web_socket_request(cls, request: web.Request) -> bool:
        ws = web.WebSocketResponse(protocols=[GRAPHQL_WS])
        return ws.can_prepare(request).ok


class HTTPHandler(BaseGraphQLView, ABC):
    async def handle_http(self, request: web.Request):
        if request.method == "GET":
            return await self.get(request)
        if request.method == "POST":
            return await self.post(request)
        raise web.HTTPMethodNotAllowed(request.method, ["GET", "POST"])

    async def get(self, request: web.Request) -> web.StreamResponse:
        if self.should_render_graphiql(request):
            return self.render_graphiql()
        return web.HTTPNotFound()

    async def post(self, request: web.Request) -> web.StreamResponse:
        request_data = await self.get_request_data(request)
        response = web.Response()
        context = await self.get_context(request, response)
        root_value = await self.get_root_value(request)

        result = await self.schema.execute(
            query=request_data.query,
            root_value=root_value,
            variable_values=request_data.variables,
            context_value=context,
            operation_name=request_data.operation_name,
        )

        response_data = await self.process_result(request, result)
        response.text = json.dumps(response_data)
        response.content_type = "application/json"
        return response

    async def get_request_data(self, request: web.Request) -> GraphQLRequestData:
        data = await self.parse_body(request)

        try:
            request_data = parse_request_data(data)
        except MissingQueryError:
            raise web.HTTPBadRequest(reason="No GraphQL query found in the request")

        return request_data

    async def parse_body(self, request: web.Request) -> dict:
        if request.content_type.startswith("multipart/form-data"):
            return await self.parse_multipart_body(request)
        try:
            return await request.json()
        except json.JSONDecodeError:
            raise web.HTTPBadRequest(reason="Unable to parse request body as JSON")

    async def parse_multipart_body(self, request: web.Request) -> dict:
        reader = await request.multipart()
        operations: Dict[str, Any] = {}
        files_map: Dict[str, Any] = {}
        files: Dict[str, Any] = {}
        try:
            async for field in reader:
                if field.name == "operations":
                    operations = (await field.json()) or {}
                elif field.name == "map":
                    files_map = (await field.json()) or {}
                elif field.filename:
                    assert field.name

                    files[field.name] = BytesIO(await field.read(decode=False))
        except ValueError:
            raise web.HTTPBadRequest(reason="Unable to parse the multipart body")
        try:
            return replace_placeholders_with_files(operations, files_map, files)
        except KeyError:
            raise web.HTTPBadRequest(reason="File(s) missing in form data")

    def render_graphiql(self) -> web.StreamResponse:
        html_string = self.graphiql_html_file_path.read_text()
        html_string = html_string.replace("{{ SUBSCRIPTION_ENABLED }}", "true")
        return web.Response(text=html_string, content_type="text/html")

    def should_render_graphiql(self, request: web.Request) -> bool:
        if not self.graphiql:
            return False
        return "text/html" in request.headers.get("Accept", "")

    @property
    def graphiql_html_file_path(self) -> Path:
        return Path(__file__).parent.parent / "static" / "graphiql.html"


class GraphQLView(HTTPHandler, WebSocketHandler, BaseGraphQLView):
    async def __call__(self, request: web.Request) -> web.StreamResponse:
        if self.is_web_socket_request(request):
            return await self.handle_web_socket(request)
        else:
            return await self.handle_http(request)
