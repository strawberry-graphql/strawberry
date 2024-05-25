"""Litestar integration for strawberry-graphql."""

from __future__ import annotations

import warnings
from datetime import timedelta
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    FrozenSet,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypedDict,
    Union,
    cast,
)

from msgspec import Struct

from litestar import (
    Controller,
    MediaType,
    Request,
    Response,
    WebSocket,
    get,
    post,
    websocket,
)
from litestar.background_tasks import BackgroundTasks
from litestar.di import Provide
from litestar.exceptions import NotFoundException, ValidationException
from litestar.status_codes import HTTP_200_OK
from strawberry.exceptions import InvalidCustomContext
from strawberry.http.async_base_view import AsyncBaseHTTPView, AsyncHTTPRequestAdapter
from strawberry.http.exceptions import HTTPException
from strawberry.http.types import FormData, HTTPMethod, QueryParams
from strawberry.http.typevars import Context, RootValue
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL
from strawberry.subscriptions.protocols.graphql_transport_ws import (
    WS_4406_PROTOCOL_NOT_ACCEPTABLE,
)

from .handlers.graphql_transport_ws_handler import (
    GraphQLTransportWSHandler as BaseGraphQLTransportWSHandler,
)
from .handlers.graphql_ws_handler import GraphQLWSHandler as BaseGraphQLWSHandler

if TYPE_CHECKING:
    from collections.abc import Mapping

    from litestar.types import AnyCallable, Dependencies
    from strawberry.http import GraphQLHTTPResponse
    from strawberry.http.ides import GraphQL_IDE
    from strawberry.schema import BaseSchema


class BaseContext(Struct, kw_only=True):
    request: Optional[Request] = None
    websocket: Optional[WebSocket] = None
    response: Optional[Response] = None


class HTTPContextType:
    """This class does not exists at runtime, it only set proper types for context attributes."""

    request: Request
    response: Response


class WebSocketContextType:
    """This class does not exists at runtime, it only set proper types for context attributes."""

    websocket: WebSocket


class HTTPContextDict(TypedDict):
    request: Request[Any, Any, Any]
    response: Response[Any]


class WebSocketContextDict(TypedDict):
    socket: WebSocket


MergedContext = Union[
    BaseContext, WebSocketContextDict, HTTPContextDict, Dict[str, Any]
]


async def _none_custom_context_getter() -> None:
    return None


async def _none_root_value_getter() -> None:
    return None


async def _context_getter_ws(
    custom_context: Optional[Any], socket: WebSocket
) -> MergedContext:
    if isinstance(custom_context, BaseContext):
        custom_context.websocket = socket
        return custom_context

    default_context = WebSocketContextDict(socket=socket)

    if isinstance(custom_context, dict):
        return {**default_context, **custom_context}

    if custom_context is None:
        return default_context

    raise InvalidCustomContext


def _response_getter() -> Response:
    return Response({}, background=BackgroundTasks([]))


async def _context_getter_http(
    custom_context: Optional[Any],
    response: Response,
    request: Request[Any, Any, Any],
) -> MergedContext:
    if isinstance(custom_context, BaseContext):
        custom_context.request = request
        custom_context.response = response
        return custom_context

    default_context = HTTPContextDict(request=request, response=response)

    if isinstance(custom_context, dict):
        return {**default_context, **custom_context}

    if custom_context is None:
        return default_context

    raise InvalidCustomContext


class GraphQLResource(Struct):
    data: Optional[dict[str, object]]
    errors: Optional[list[object]]
    extensions: Optional[dict[str, object]]


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


class LitestarRequestAdapter(AsyncHTTPRequestAdapter):
    def __init__(self, request: Request[Any, Any, Any]) -> None:
        self.request = request

    @property
    def query_params(self) -> QueryParams:
        return self.request.query_params

    @property
    def method(self) -> HTTPMethod:
        return cast(HTTPMethod, self.request.method.upper())

    @property
    def headers(self) -> Mapping[str, str]:
        return self.request.headers

    @property
    def content_type(self) -> Optional[str]:
        return self.request.content_type[0]

    async def get_body(self) -> bytes:
        return await self.request.body()

    async def get_form_data(self) -> FormData:
        multipart_data = await self.request.form()

        return FormData(form=multipart_data, files=multipart_data)


class GraphQLController(
    Controller,
    AsyncBaseHTTPView[
        Request[Any, Any, Any], Response[Any], Response[Any], Context, RootValue
    ],
):
    path: str = ""
    dependencies: Dependencies = {
        "custom_context": Provide(_none_custom_context_getter),
        "context": Provide(_context_getter_http),
        "context_ws": Provide(_context_getter_ws),
        "root_value": Provide(_none_root_value_getter),
        "response": Provide(_response_getter, sync_to_thread=True),
    }

    request_adapter_class = LitestarRequestAdapter
    graphql_ws_handler_class: Type[GraphQLWSHandler] = GraphQLWSHandler
    graphql_transport_ws_handler_class: Type[GraphQLTransportWSHandler] = (
        GraphQLTransportWSHandler
    )

    allow_queries_via_get: bool = True
    graphiql_allowed_accept: FrozenSet[str] = frozenset({"text/html", "*/*"})
    graphql_ide: Optional[GraphQL_IDE] = "graphiql"
    debug: bool = False
    connection_init_wait_timeout: timedelta = timedelta(minutes=1)
    protocols: Tuple[str, ...] = (
        GRAPHQL_TRANSPORT_WS_PROTOCOL,
        GRAPHQL_WS_PROTOCOL,
    )
    keep_alive: bool = False
    keep_alive_interval: float = 1

    async def execute_request(
        self,
        request: Request[Any, Any, Any],
        context: Any,
        root_value: Any,
    ) -> Response[Union[GraphQLResource, str]]:
        try:
            return await self.run(
                request,
                # TODO: check the dependency, above, can we make it so that
                # we don't need to type ignore here?
                context=context,
                root_value=root_value,
            )
        except HTTPException as e:
            return Response(
                e.reason,
                status_code=e.status_code,
                media_type=MediaType.TEXT,
            )

    async def render_graphql_ide(
        self, request: Request[Any, Any, Any]
    ) -> Response[str]:
        return Response(self.graphql_ide_html, media_type=MediaType.HTML)

    def create_response(
        self, response_data: GraphQLHTTPResponse, sub_response: Response[bytes]
    ) -> Response[bytes]:
        response = Response(
            self.encode_json(response_data).encode(),
            status_code=HTTP_200_OK,
            media_type=MediaType.JSON,
        )

        response.headers.update(sub_response.headers)
        response.cookies.extend(sub_response.cookies)
        response.background = sub_response.background

        if sub_response.status_code:
            response.status_code = sub_response.status_code

        return response

    @get(raises=[ValidationException, NotFoundException])
    async def handle_http_get(
        self,
        request: Request[Any, Any, Any],
        context: Any,
        root_value: Any,
        response: Response,
    ) -> Response[Union[GraphQLResource, str]]:
        self.temporal_response = response

        return await self.execute_request(
            request=request,
            context=context,
            root_value=root_value,
        )

    @post(status_code=HTTP_200_OK)
    async def handle_http_post(
        self,
        request: Request[Any, Any, Any],
        context: Any,
        root_value: Any,
        response: Response,
    ) -> Response[Union[GraphQLResource, str]]:
        self.temporal_response = response

        return await self.execute_request(
            request=request,
            context=context,
            root_value=root_value,
        )

    async def get_context(
        self, request: Request[Any, Any, Any], response: Response
    ) -> Context:  # pragma: no cover
        msg = "`get_context` is not used by Litestar's controller"
        raise ValueError(msg)

    async def get_root_value(
        self, request: Request[Any, Any, Any]
    ) -> RootValue | None:  # pragma: no cover
        msg = "`get_root_value` is not used by Litestar's controller"
        raise ValueError(msg)

    async def get_sub_response(self, request: Request[Any, Any, Any]) -> Response:
        return self.temporal_response

    @websocket()
    async def websocket_endpoint(
        self,
        socket: WebSocket,
        context_ws: Any,
        root_value: Any,
    ) -> None:
        async def _get_context() -> Any:
            return context_ws

        async def _get_root_value() -> Any:
            return root_value

        preferred_protocol = self.pick_preferred_protocol(socket)
        if preferred_protocol == GRAPHQL_TRANSPORT_WS_PROTOCOL:
            await self.graphql_transport_ws_handler_class(
                schema=self.schema,
                debug=self.debug,
                connection_init_wait_timeout=self.connection_init_wait_timeout,
                get_context=_get_context,
                get_root_value=_get_root_value,
                ws=socket,
            ).handle()
        elif preferred_protocol == GRAPHQL_WS_PROTOCOL:
            await self.graphql_ws_handler_class(
                schema=self.schema,
                debug=self.debug,
                keep_alive=self.keep_alive,
                keep_alive_interval=self.keep_alive_interval,
                get_context=_get_context,
                get_root_value=_get_root_value,
                ws=socket,
            ).handle()
        else:
            await socket.close(code=WS_4406_PROTOCOL_NOT_ACCEPTABLE)

    def pick_preferred_protocol(self, socket: WebSocket) -> str | None:
        protocols: List[str] = socket.scope["subprotocols"]
        intersection: Set[str] = set(protocols) & set(self.protocols)
        return (
            min(
                intersection,
                key=lambda i: protocols.index(i) if i else "",
                default=None,
            )
            or None
        )


def make_graphql_controller(
    schema: BaseSchema,
    path: str = "",
    graphiql: Optional[bool] = None,
    graphql_ide: Optional[GraphQL_IDE] = "graphiql",
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
) -> Type[GraphQLController]:  # sourcery skip: move-assign
    if context_getter is None:
        custom_context_getter_ = _none_custom_context_getter
    else:
        custom_context_getter_ = context_getter

    if root_value_getter is None:
        root_value_getter_ = _none_root_value_getter
    else:
        root_value_getter_ = root_value_getter

    schema_: BaseSchema = schema
    allow_queries_via_get_: bool = allow_queries_via_get
    graphql_ide_: Optional[GraphQL_IDE]

    if graphiql is not None:
        warnings.warn(
            "The `graphiql` argument is deprecated in favor of `graphql_ide`",
            DeprecationWarning,
            stacklevel=2,
        )
        graphql_ide_ = "graphiql" if graphiql else None
    else:
        graphql_ide_ = graphql_ide

    routes_path: str = path

    class _GraphQLController(GraphQLController):
        path: str = routes_path
        dependencies: Dependencies = {
            "custom_context": Provide(custom_context_getter_),
            "context": Provide(_context_getter_http),
            "context_ws": Provide(_context_getter_ws),
            "root_value": Provide(root_value_getter_),
            "response": Provide(_response_getter, sync_to_thread=True),
        }

    _GraphQLController.keep_alive = keep_alive
    _GraphQLController.keep_alive_interval = keep_alive_interval
    _GraphQLController.debug = debug
    _GraphQLController.protocols = subscription_protocols
    _GraphQLController.connection_init_wait_timeout = connection_init_wait_timeout
    _GraphQLController.graphiql_allowed_accept = frozenset({"text/html", "*/*"})
    _GraphQLController.schema = schema_
    _GraphQLController.allow_queries_via_get = allow_queries_via_get_
    _GraphQLController.graphql_ide = graphql_ide_

    return _GraphQLController
