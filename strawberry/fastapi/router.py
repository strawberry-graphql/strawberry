import json
from datetime import timedelta
from inspect import signature
from typing import Any, Callable, Dict, Optional, Sequence, Union

from starlette import status
from starlette.background import BackgroundTasks
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response
from starlette.types import ASGIApp
from starlette.websockets import WebSocket

from fastapi import APIRouter, Depends
from strawberry.asgi.utils import get_graphiql_html
from strawberry.exceptions import InvalidCustomContext, MissingQueryError
from strawberry.fastapi.handlers import GraphQLTransportWSHandler, GraphQLWSHandler
from strawberry.file_uploads.utils import replace_placeholders_with_files
from strawberry.http import GraphQLHTTPResponse, parse_request_data, process_result
from strawberry.schema import BaseSchema
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL
from strawberry.types import ExecutionResult
from strawberry.utils.debug import pretty_print_graphql_operation


CustomContext = Union["BaseContext", Dict[str, Any]]
MergedContext = Union[
    "BaseContext", Dict[str, Union[Any, BackgroundTasks, Request, Response, WebSocket]]
]


class BaseContext:
    def __init__(self):
        self.request: Optional[Union[Request, WebSocket]] = None
        self.background_tasks: Optional[BackgroundTasks] = None
        self.response: Optional[Response] = None


class GraphQLRouter(APIRouter):
    graphql_ws_handler_class = GraphQLWSHandler
    graphql_transport_ws_handler_class = GraphQLTransportWSHandler

    @staticmethod
    async def __get_root_value():
        return None

    @staticmethod
    def __get_context_getter(
        custom_getter: Callable[..., Optional[CustomContext]]
    ) -> Callable[..., CustomContext]:
        def dependency(
            custom_getter: Optional[CustomContext],
            background_tasks: BackgroundTasks,
            request: Request = None,
            response: Response = None,
            ws: WebSocket = None,
        ) -> MergedContext:
            default_context = {
                "request": request or ws,
                "background_tasks": background_tasks,
                "response": response,
            }
            if isinstance(custom_getter, BaseContext):
                custom_getter.request = request or ws
                custom_getter.background_tasks = background_tasks
                custom_getter.response = response
                return custom_getter
            elif isinstance(custom_getter, dict):
                return {
                    **default_context,
                    **custom_getter,
                }
            elif custom_getter is None:
                return default_context
            else:
                raise InvalidCustomContext()

        # replace the signature parameters of dependency...
        # ...with the old parameters minus the first argument as it will be replaced...
        # ...with the value obtained by injecting custom_getter context as a dependency.
        sig = signature(dependency)
        sig = sig.replace(
            parameters=[
                *list(sig.parameters.values())[1:],
                sig.parameters["custom_getter"].replace(default=Depends(custom_getter)),
            ],
        )
        # there is an ongoing issue with types and .__signature__ applied to Callables:
        # https://github.com/python/mypy/issues/5958, as of 14/12/21
        # as such, the below line has its typing ignored by MyPy
        dependency.__signature__ = sig  # type: ignore
        return dependency

    def __init__(
        self,
        schema: BaseSchema,
        path: str = "",
        graphiql: bool = True,
        keep_alive: bool = False,
        keep_alive_interval: float = 1,
        debug: bool = False,
        root_value_getter=None,
        context_getter=None,
        subscription_protocols=(GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL),
        connection_init_wait_timeout: timedelta = timedelta(minutes=1),
        default: Optional[ASGIApp] = None,
        on_startup: Optional[Sequence[Callable[[], Any]]] = None,
        on_shutdown: Optional[Sequence[Callable[[], Any]]] = None,
    ):
        super().__init__(
            default=default,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
        )
        self.schema = schema
        self.graphiql = graphiql
        self.keep_alive = keep_alive
        self.keep_alive_interval = keep_alive_interval
        self.debug = debug
        self.root_value_getter = root_value_getter or self.__get_root_value
        self.context_getter = self.__get_context_getter(
            context_getter or (lambda: None)
        )
        self.protocols = subscription_protocols
        self.connection_init_wait_timeout = connection_init_wait_timeout

        @self.get(
            path,
            responses={
                200: {
                    "description": "The GraphiQL integrated development environment.",
                },
                404: {
                    "description": "Not found if GraphiQL is not enabled.",
                },
            },
        )
        async def get_graphiql() -> Response:
            if not self.graphiql:
                return Response(status_code=status.HTTP_404_NOT_FOUND)
            return self.get_graphiql_response()

        @self.post(path)
        async def handle_http_query(
            request: Request,
            response: Response,
            context=Depends(self.context_getter),
            root_value=Depends(self.root_value_getter),
        ) -> Response:
            actual_response: Response

            content_type = request.headers.get("content-type", "")

            if "application/json" in content_type:
                try:
                    data = await request.json()
                except json.JSONDecodeError:
                    actual_response = PlainTextResponse(
                        "Unable to parse request body as JSON",
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )

                    return self._merge_responses(response, actual_response)
            elif content_type.startswith("multipart/form-data"):
                multipart_data = await request.form()
                operations = json.loads(multipart_data.get("operations", {}))
                files_map = json.loads(multipart_data.get("map", {}))
                data = replace_placeholders_with_files(
                    operations, files_map, multipart_data
                )
            else:
                actual_response = PlainTextResponse(
                    "Unsupported Media Type",
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                )

                return self._merge_responses(response, actual_response)

            try:
                request_data = parse_request_data(data)
            except MissingQueryError:
                actual_response = PlainTextResponse(
                    "No GraphQL query found in the request",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
                return self._merge_responses(response, actual_response)

            result = await self.execute(
                request_data.query,
                variables=request_data.variables,
                context=context,
                operation_name=request_data.operation_name,
                root_value=root_value,
            )

            response_data = await self.process_result(request, result)

            actual_response = JSONResponse(
                response_data,
                status_code=status.HTTP_200_OK,
            )

            return self._merge_responses(response, actual_response)

        @self.websocket(path)
        async def websocket_endpoint(
            websocket: WebSocket,
            context=Depends(self.context_getter),
            root_value=Depends(self.root_value_getter),
        ):
            async def _get_context():
                return context

            async def _get_root_value():
                return root_value

            preferred_protocol = self.pick_preferred_protocol(websocket)
            if preferred_protocol == GRAPHQL_TRANSPORT_WS_PROTOCOL:
                await self.graphql_transport_ws_handler_class(
                    schema=self.schema,
                    debug=self.debug,
                    connection_init_wait_timeout=self.connection_init_wait_timeout,
                    get_context=_get_context,
                    get_root_value=_get_root_value,
                    ws=websocket,
                ).handle()
            elif preferred_protocol == GRAPHQL_WS_PROTOCOL:
                await self.graphql_ws_handler_class(
                    schema=self.schema,
                    debug=self.debug,
                    keep_alive=self.keep_alive,
                    keep_alive_interval=self.keep_alive_interval,
                    get_context=_get_context,
                    get_root_value=_get_root_value,
                    ws=websocket,
                ).handle()
            else:
                # Code 4406 is "Subprotocol not acceptable"
                await websocket.close(code=4406)

    def pick_preferred_protocol(self, ws: WebSocket) -> Optional[str]:
        protocols = ws["subprotocols"]
        intersection = set(protocols) & set(self.protocols)
        return min(
            intersection,
            key=lambda i: protocols.index(i),  # type: ignore
            default=None,
        )

    def get_graphiql_response(self) -> HTMLResponse:
        html = get_graphiql_html()
        return HTMLResponse(html)

    @staticmethod
    def _merge_responses(response: Response, actual_response: Response) -> Response:
        actual_response.headers.raw.extend(response.headers.raw)
        if response.status_code:
            actual_response.status_code = response.status_code

        return actual_response

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

    async def process_result(
        self, request: Request, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        return process_result(result)
