"""Starlite integration for strawberry-graphql."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING, Any, Dict, Optional, Union, cast

from starlite import (
    BackgroundTasks,
    Controller,
    HttpMethod,
    MediaType,
    Provide,
    Request,
    Response,
    WebSocket,
    get,
    post,
    websocket,
)
from starlite.exceptions import (
    NotFoundException,
    SerializationException,
    ValidationException,
)
from starlite.status_codes import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_415_UNSUPPORTED_MEDIA_TYPE,
)
from strawberry.exceptions import InvalidCustomContext, MissingQueryError
from strawberry.file_uploads.utils import replace_placeholders_with_files
from strawberry.http import (
    GraphQLHTTPResponse,
    parse_query_params,
    parse_request_data,
    process_result,
)
from strawberry.schema.exceptions import InvalidOperationTypeError
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL
from strawberry.subscriptions.protocols.graphql_transport_ws import (
    WS_4406_PROTOCOL_NOT_ACCEPTABLE,
)
from strawberry.types.graphql import OperationType
from strawberry.utils.debug import pretty_print_graphql_operation
from strawberry.utils.graphiql import get_graphiql_html

from .handlers.graphql_transport_ws_handler import (
    GraphQLTransportWSHandler as BaseGraphQLTransportWSHandler,
)
from .handlers.graphql_ws_handler import GraphQLWSHandler as BaseGraphQLWSHandler

if TYPE_CHECKING:
    from typing import FrozenSet, Iterable, List, Set, Tuple, Type

    from starlite.types import AnyCallable, Dependencies
    from strawberry.schema import BaseSchema
    from strawberry.types import ExecutionResult

    MergedContext = Union[
        "BaseContext",
        Union[
            Dict[str, Any],
            Dict[str, BackgroundTasks],
            Dict[str, Request],
            Dict[str, Response],
            Dict[str, websocket],
        ],
    ]

CustomContext = Union["BaseContext", Dict[str, Any]]


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
    if custom_context is None:
        return default_context
    raise InvalidCustomContext()


@dataclass
class GraphQLResource:
    data: Optional[Dict[str, object]]
    errors: Optional[List[object]]
    extensions: Optional[Dict[str, object]]


@dataclass
class EmptyResponseModel:
    pass


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
        self.response: Optional[Response] = None


def make_graphql_controller(
    schema: BaseSchema,
    path: str = "",
    graphiql: bool = True,
    allow_queries_via_get: bool = True,
    keep_alive: bool = False,
    keep_alive_interval: float = 1,
    debug: bool = False,
    # TODO: root typevar
    root_value_getter: Optional[AnyCallable] = None,
    # TODO: context typevar
    context_getter: Optional[AnyCallable] = None,
    subscription_protocols: Tuple[str, ...] = (
        GRAPHQL_TRANSPORT_WS_PROTOCOL,
        GRAPHQL_WS_PROTOCOL,
    ),
    connection_init_wait_timeout: timedelta = timedelta(minutes=1),
) -> Type[Controller]:
    routes_path = path

    if context_getter is None:

        def custom_context_getter_():
            return None

    else:
        custom_context_getter_ = context_getter

    if root_value_getter is None:

        def root_value_getter_():
            return None

    else:
        root_value_getter_ = root_value_getter

    class GraphQLController(Controller):
        path: str = routes_path
        dependencies: Optional[Dependencies] = {
            "custom_context": Provide(custom_context_getter_),
            "context": Provide(_context_getter),
            "root_value": Provide(root_value_getter_),
        }
        graphql_ws_handler_class: Type[GraphQLWSHandler] = GraphQLWSHandler
        graphql_transport_ws_handler_class: Type[
            GraphQLTransportWSHandler
        ] = GraphQLTransportWSHandler

        _schema: BaseSchema = schema
        _graphiql: bool = graphiql
        _allow_queries_via_get: bool = allow_queries_via_get
        _keep_alive: bool = keep_alive
        _keep_alive_interval: float = keep_alive_interval
        _debug: bool = debug
        _protocols: Tuple[str, ...] = subscription_protocols
        _connection_init_wait_timeout: timedelta = connection_init_wait_timeout
        _graphiql_allowed_accept: FrozenSet[str] = frozenset({"text/html", "*/*"})

        async def execute(
            self,
            query: Optional[str],
            variables: Optional[Dict[str, Any]] = None,
            context: Optional[CustomContext] = None,
            operation_name: Optional[str] = None,
            root_value: Optional[Any] = None,
            allowed_operation_types: Optional[Iterable[OperationType]] = None,
        ):
            if self._debug:
                pretty_print_graphql_operation(operation_name, query or "", variables)

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
            self,
            request: Request,
            data: dict,
            context: CustomContext,
            root_value: Any,
        ) -> Response[Union[GraphQLResource, str]]:
            request_data = parse_request_data(data or {})

            allowed_operation_types = OperationType.from_http(request.method)

            if not self._allow_queries_via_get and request.method == HttpMethod.GET:
                allowed_operation_types = allowed_operation_types - {
                    OperationType.QUERY
                }

            response: Union[Response[dict], Response[BaseContext]] = Response(
                {}, background=BackgroundTasks([])
            )

            if isinstance(context, BaseContext):
                context.response = response
            elif isinstance(context, dict):
                context["response"] = response
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
                    e.as_http_error_reason(request.method),
                    status_code=HTTP_400_BAD_REQUEST,
                    media_type=MediaType.TEXT,
                )
            except MissingQueryError:
                return Response(
                    "No GraphQL query found in the request",
                    status_code=HTTP_400_BAD_REQUEST,
                    media_type=MediaType.TEXT,
                )

            response_data = await self.process_result(result)

            actual_response: Response[GraphQLHTTPResponse] = Response(
                response_data, status_code=HTTP_200_OK, media_type=MediaType.JSON
            )

            return self._merge_responses(response, actual_response)

        def should_render_graphiql(self, request: Request) -> bool:
            if not self._graphiql:
                return False
            accept: Set[str] = set()
            for value in request.headers.getall("accept", ""):
                accept.symmetric_difference_update(set(value.split(",")))
            return bool(self._graphiql_allowed_accept & accept)

        def get_graphiql_response(self) -> Response[str]:
            html = get_graphiql_html()
            return Response(html, media_type=MediaType.HTML)

        @staticmethod
        def _merge_responses(
            response: Response, actual_response: Response
        ) -> Response[Union[GraphQLResource, str]]:
            actual_response.headers.update(response.headers)
            actual_response.cookies.extend(response.cookies)
            actual_response.background = response.background
            if response.status_code:
                actual_response.status_code = response.status_code

            return actual_response

        @get(raises=[ValidationException, NotFoundException])
        async def handle_http_get(
            self,
            request: Request,
            context: CustomContext,
            root_value: Any,
        ) -> Response[Union[GraphQLResource, str]]:
            if request.query_params:
                try:
                    query_data = parse_query_params(
                        cast("Dict[str, Any]", request.query_params)
                    )
                except json.JSONDecodeError as error:
                    raise ValidationException(
                        detail="Unable to parse request body as JSON"
                    ) from error
                return await self.execute_request(
                    request=request,
                    data=query_data,
                    context=context,
                    root_value=root_value,
                )
            if self.should_render_graphiql(request):
                return cast(
                    "Response[Union[GraphQLResource, str]]",
                    self.get_graphiql_response(),
                )
            raise NotFoundException()

        @post(status_code=HTTP_200_OK)
        async def handle_http_post(
            self,
            request: Request,
            context: CustomContext,
            root_value: Any,
        ) -> Response[Union[GraphQLResource, str]]:
            actual_response: Response[Union[GraphQLResource, str]]

            content_type, _ = request.content_type

            if "application/json" in content_type:
                try:
                    data = await request.json()
                except SerializationException:
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
                try:
                    data = replace_placeholders_with_files(
                        operations, files_map, multipart_data
                    )
                except KeyError:
                    return Response(
                        "File(s) missing in form data",
                        status_code=HTTP_400_BAD_REQUEST,
                        media_type=MediaType.TEXT,
                    )
                except (TypeError, AttributeError):
                    return Response(
                        "Unable to parse the multipart body",
                        status_code=HTTP_400_BAD_REQUEST,
                        media_type=MediaType.TEXT,
                    )
            else:
                return Response(
                    "Unsupported Media Type",
                    status_code=HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    media_type=MediaType.TEXT,
                )

            return await self.execute_request(
                request=request,
                data=data,
                context=context,
                root_value=root_value,
            )

        @websocket()
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
                await socket.close(code=WS_4406_PROTOCOL_NOT_ACCEPTABLE)

        def pick_preferred_protocol(self, socket: WebSocket) -> Optional[str]:
            protocols: List[str] = socket.scope["subprotocols"]
            intersection = set(protocols) & set(self._protocols)
            return (
                min(
                    intersection,
                    key=lambda i: protocols.index(i) if i else "",
                    default=None,
                )
                or None
            )

    return GraphQLController
