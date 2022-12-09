"""Starlite integration for strawberry-graphql."""
import json
from datetime import timedelta
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Type, Union, cast

from starlite import (
    BackgroundTasks,
    Controller,
    MediaType,
    Provide,
    Request,
    Response,
    WebSocket,
    get,
    post,
    websocket,
)
from starlite.exceptions import ImproperlyConfiguredException
from starlite.status_codes import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_415_UNSUPPORTED_MEDIA_TYPE,
)
from starlite.types import AnyCallable
from strawberry.exceptions import InvalidCustomContext, MissingQueryError
from strawberry.file_uploads.utils import replace_placeholders_with_files
from strawberry.http import (
    GraphQLHTTPResponse,
    parse_query_params,
    parse_request_data,
    process_result,
)
from strawberry.schema import BaseSchema
from strawberry.schema.exceptions import InvalidOperationTypeError
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL
from strawberry.types import ExecutionResult
from strawberry.types.graphql import OperationType
from strawberry.utils.debug import pretty_print_graphql_operation
from strawberry.utils.graphiql import get_graphiql_html

from .handlers.graphql_transport_ws_handler import (
    GraphQLTransportWSHandler as BaseGraphQLTransportWSHandler,
)
from .handlers.graphql_ws_handler import GraphQLWSHandler as BaseGraphQLWSHandler


if TYPE_CHECKING:
    from starlite.types import Dependencies


CustomContext = Union["BaseContext", Dict[str, Any]]
MergedContext = Union[
    "BaseContext", Dict[str, Union[Any, BackgroundTasks, Request, Response, WebSocket]]
]


def _get_root_value_getter(custom_root_value: Union[AnyCallable, None]) -> Any:
    if custom_root_value is not None:
        return custom_root_value
    return None


async def _context_getter(
    custom_context: Optional[CustomContext],
    request: Request,
) -> MergedContext:
    if isinstance(custom_context, BaseContext):
        custom_context.request = request
        return custom_context
    default_context = {
        "request": request,
    }
    if isinstance(custom_context, dict):
        return {
            **default_context,
            **custom_context,
        }
    elif custom_context is None:
        return default_context
    else:
        raise InvalidCustomContext()


class GraphQLWSHandler(BaseGraphQLWSHandler):
    async def get_context(self) -> Any:
        return await self._get_context()

    async def get_root_value(self) -> Any:
        return await self._get_root_value()


class GraphQLTransportWSHandler(BaseGraphQLTransportWSHandler):
    async def get_context(self) -> Any:
        return await self._get_context()

    async def get_root_value(self) -> Any:
        return await self._get_root_value()


class BaseContext:
    def __init__(self):
        self.request: Optional[Union[Request, WebSocket]] = None


def make_graphql_controller(
    schema: BaseSchema,
    path: str = "",
    websocket_path: str = "/ws",
    graphiql: bool = True,
    allow_queries_via_get: bool = True,
    keep_alive: bool = False,
    keep_alive_interval: float = 1,
    debug: bool = False,
    root_value_getter=None,
    context_getter=None,
    subscription_protocols=(GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL),
    connection_init_wait_timeout: timedelta = timedelta(minutes=1),
) -> Type[Controller]:
    routes_path = path

    if not websocket_path:
        raise ImproperlyConfiguredException(detail="webocket_path must not be empty")

    if context_getter is None:

        def context_getter_():
            return None

    else:
        context_getter_ = context_getter

    if root_value_getter is None:

        def root_value_getter_():
            return None

    else:
        root_value_getter_ = root_value_getter

    class GraphQLController(Controller):
        path: str = routes_path
        dependencies: Optional["Dependencies"] = {
            "custom_context": Provide(context_getter_),
            "context": Provide(_context_getter),
            "root_value": Provide(root_value_getter_),
        }
        graphql_ws_handler_class = GraphQLWSHandler
        graphql_transport_ws_handler_class = GraphQLTransportWSHandler

        _schema: BaseSchema = schema
        _graphiql: bool = graphiql
        _allow_queries_via_get: bool = allow_queries_via_get
        _keep_alive: bool = keep_alive
        _keep_alive_interval: float = keep_alive_interval
        _debug: bool = debug
        _protocols = subscription_protocols
        _connection_init_wait_timeout: timedelta = connection_init_wait_timeout

        async def execute(
            self,
            query: str,
            variables: Optional[Dict[str, Any]] = None,
            context: Any = None,
            operation_name: Optional[str] = None,
            root_value: Any = None,
            allowed_operation_types: Optional[Iterable[OperationType]] = None,
        ):
            if self._debug:
                pretty_print_graphql_operation(operation_name, query, variables)

            return await self._schema.execute(
                query,
                root_value=root_value,
                variable_values=variables,
                operation_name=operation_name,
                context_value=context,
                allowed_operation_types=allowed_operation_types,
            )

        async def process_result(self, result: ExecutionResult) -> GraphQLHTTPResponse:
            return process_result(result)

        async def execute_request(
            self, request: Request, data: dict, context, root_value
        ) -> Response:
            try:
                request_data = parse_request_data(data or {})
            except MissingQueryError:
                missing_query_response = Response(
                    "No GraphQL query found in the request",
                    status_code=HTTP_400_BAD_REQUEST,
                    media_type=MediaType.TEXT,
                )
                return missing_query_response

            method = request.method
            allowed_operation_types = OperationType.from_http(method)

            if not self._allow_queries_via_get and method == "GET":
                allowed_operation_types = allowed_operation_types - {
                    OperationType.QUERY
                }

            try:
                result = await self.execute(
                    request_data.query,
                    variables=request_data.variables,
                    context=context,
                    operation_name=request_data.operation_name,
                    root_value=root_value,
                    allowed_operation_types=allowed_operation_types,
                )
            except InvalidOperationTypeError as e:
                return Response(
                    e.as_http_error_reason(method),
                    status_code=HTTP_400_BAD_REQUEST,
                    media_type=MediaType.TEXT,
                )

            response_data = await self.process_result(result)

            actual_response: Response = Response(
                response_data, status_code=HTTP_200_OK, media_type=MediaType.JSON
            )

            return actual_response

        def should_render_graphiql(self, request: Request) -> bool:
            if not self._graphiql:
                return False
            return any(
                supported_header in request.headers.get("accept", "")
                for supported_header in ("text/html", "*/*")
            )

        def get_graphiql_response(self) -> Response:
            html = get_graphiql_html()
            return Response(html, media_type=MediaType.HTML)

        @get()
        async def handle_http_get(
            self,
            request: Request,
            context: CustomContext,
            root_value: Any,
        ) -> Response:
            actual_response: Response

            if request.query_params:
                query_data = parse_query_params(
                    cast(Dict[str, Any], request.query_params)
                )
                return await self.execute_request(
                    request=request,
                    data=query_data,
                    context=context,
                    root_value=root_value,
                )
            elif self.should_render_graphiql(request):
                return self.get_graphiql_response()
            return Response(content="Bad request", status_code=HTTP_400_BAD_REQUEST)

        @post()
        async def handle_http_post(
            self,
            request: Request,
            context: CustomContext,
            root_value: Any,
        ) -> Response:
            actual_response: Response

            content_type = request.headers.get("content-type", "")

            if "application/json" in content_type:
                try:
                    data = await request.json()
                except json.JSONDecodeError:
                    actual_response = Response(
                        "Unable to parse request body as JSON",
                        status_code=HTTP_400_BAD_REQUEST,
                        media_type=MediaType.TEXT,
                    )
                    return actual_response
            elif content_type.startswith("multipart/form-data"):
                multipart_data = await request.form()
                operations: Dict[str, Any] = multipart_data.get("operations", "{}")
                files_map: Dict[str, List[str]] = multipart_data.get("map", "{}")
                data = replace_placeholders_with_files(
                    operations, files_map, multipart_data
                )
            else:
                actual_response = Response(
                    "Unsupported Media Type",
                    status_code=HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    media_type=MediaType.TEXT,
                )
                return actual_response

            return await self.execute_request(
                request=request,
                data=data,
                context=context,
                root_value=root_value,
            )

        @websocket(websocket_path)
        async def websocket_endpoint(
            self,
            socket: WebSocket,
            context: CustomContext,
            root_value: Any,
        ) -> None:
            async def _get_context():
                return context

            async def _get_root_value():
                return root_value

            preferred_protocol = self.pick_preferred_protocol(socket)
            if preferred_protocol == GRAPHQL_TRANSPORT_WS_PROTOCOL:
                await self.graphql_transport_ws_handler_class(
                    schema=self._schema,
                    debug=self._debug,
                    connection_init_wait_timeout=self._connection_init_wait_timeout,
                    get_context=_get_context,
                    get_root_value=_get_root_value,
                    ws=socket,
                ).handle()
            elif preferred_protocol == GRAPHQL_WS_PROTOCOL:
                await self.graphql_ws_handler_class(
                    schema=self._schema,
                    debug=self._debug,
                    keep_alive=self._keep_alive,
                    keep_alive_interval=self._keep_alive_interval,
                    get_context=_get_context,
                    get_root_value=_get_root_value,
                    ws=socket,
                ).handle()
            else:
                # Code 4406 is "Subprotocol not acceptable"
                await socket.close(code=4406)

        def pick_preferred_protocol(self, socket: WebSocket) -> Optional[str]:
            protocols = socket.scope["subprotocols"]
            intersection = set(protocols) & set(self._protocols)
            return min(
                intersection,
                key=lambda i: protocols.index(i),
                default=None,
            )

    return GraphQLController
