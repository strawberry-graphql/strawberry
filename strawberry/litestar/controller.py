"""Litestar integration for strawberry-graphql."""

from __future__ import annotations

import json
import warnings
from datetime import timedelta
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Optional,
    TypedDict,
    Union,
    cast,
)
from typing_extensions import TypeGuard

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
from litestar.exceptions import (
    NotFoundException,
    ValidationException,
    WebSocketDisconnect,
)
from litestar.response.streaming import Stream
from litestar.status_codes import HTTP_200_OK
from strawberry.exceptions import InvalidCustomContext
from strawberry.http.async_base_view import (
    AsyncBaseHTTPView,
    AsyncHTTPRequestAdapter,
    AsyncWebSocketAdapter,
)
from strawberry.http.exceptions import (
    HTTPException,
    NonJsonMessageReceived,
    NonTextMessageReceived,
    WebSocketDisconnected,
)
from strawberry.http.types import FormData, HTTPMethod, QueryParams
from strawberry.http.typevars import Context, RootValue
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, AsyncIterator, Mapping

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
    BaseContext, WebSocketContextDict, HTTPContextDict, dict[str, Any]
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
        content_type, params = self.request.content_type

        # combine content type and params
        if params:
            content_type += "; " + "; ".join(f"{k}={v}" for k, v in params.items())

        return content_type

    async def get_body(self) -> bytes:
        return await self.request.body()

    async def get_form_data(self) -> FormData:
        multipart_data = await self.request.form()

        return FormData(form=multipart_data, files=multipart_data)


class LitestarWebSocketAdapter(AsyncWebSocketAdapter):
    def __init__(
        self, view: AsyncBaseHTTPView, request: WebSocket, response: WebSocket
    ) -> None:
        super().__init__(view)
        self.ws = response

    async def iter_json(
        self, *, ignore_parsing_errors: bool = False
    ) -> AsyncGenerator[object, None]:
        try:
            while self.ws.connection_state != "disconnect":
                text = await self.ws.receive_text()

                # Litestar internally defaults to an empty string for non-text messages
                if text == "":
                    raise NonTextMessageReceived

                try:
                    yield self.view.decode_json(text)
                except json.JSONDecodeError as e:
                    if not ignore_parsing_errors:
                        raise NonJsonMessageReceived from e
        except WebSocketDisconnect:
            pass

    async def send_json(self, message: Mapping[str, object]) -> None:
        try:
            await self.ws.send_data(data=self.view.encode_json(message))
        except WebSocketDisconnect as exc:
            raise WebSocketDisconnected from exc

    async def close(self, code: int, reason: str) -> None:
        await self.ws.close(code=code, reason=reason)


class GraphQLController(
    Controller,
    AsyncBaseHTTPView[
        Request[Any, Any, Any],
        Response[Any],
        Response[Any],
        WebSocket,
        WebSocket,
        Context,
        RootValue,
    ],
):
    path: str = ""
    dependencies: ClassVar[Dependencies] = {  # type: ignore[misc]
        "custom_context": Provide(_none_custom_context_getter),
        "context": Provide(_context_getter_http),
        "context_ws": Provide(_context_getter_ws),
        "root_value": Provide(_none_root_value_getter),
        "response": Provide(_response_getter, sync_to_thread=True),
    }

    request_adapter_class = LitestarRequestAdapter
    websocket_adapter_class = LitestarWebSocketAdapter

    allow_queries_via_get: bool = True
    graphiql_allowed_accept: frozenset[str] = frozenset({"text/html", "*/*"})
    graphql_ide: Optional[GraphQL_IDE] = "graphiql"
    debug: bool = False
    connection_init_wait_timeout: timedelta = timedelta(minutes=1)
    protocols: tuple[str, ...] = (
        GRAPHQL_TRANSPORT_WS_PROTOCOL,
        GRAPHQL_WS_PROTOCOL,
    )
    keep_alive: bool = False
    keep_alive_interval: float = 1

    def is_websocket_request(
        self, request: Union[Request, WebSocket]
    ) -> TypeGuard[WebSocket]:
        return isinstance(request, WebSocket)

    async def pick_websocket_subprotocol(self, request: WebSocket) -> Optional[str]:
        subprotocols = request.scope["subprotocols"]
        intersection = set(subprotocols) & set(self.protocols)
        sorted_intersection = sorted(intersection, key=subprotocols.index)
        return next(iter(sorted_intersection), None)

    async def create_websocket_response(
        self, request: WebSocket, subprotocol: Optional[str]
    ) -> WebSocket:
        await request.accept(subprotocols=subprotocol)
        return request

    async def execute_request(
        self,
        request: Request[Any, Any, Any],
        context: Any,
        root_value: Any,
    ) -> Response[Union[GraphQLResource, str]]:
        try:
            return await self.run(
                request,
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

    async def create_streaming_response(
        self,
        request: Request,
        stream: Callable[[], AsyncIterator[str]],
        sub_response: Response,
        headers: dict[str, str],
    ) -> Response:
        return Stream(
            stream(),
            status_code=sub_response.status_code,
            headers={
                **sub_response.headers,
                **headers,
            },
        )

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

    @websocket()
    async def websocket_endpoint(
        self,
        socket: WebSocket,
        context_ws: Any,
        root_value: Any,
    ) -> None:
        await self.run(
            request=socket,
            context=context_ws,
            root_value=root_value,
        )

    async def get_context(
        self,
        request: Union[Request[Any, Any, Any], WebSocket],
        response: Union[Response, WebSocket],
    ) -> Context:  # pragma: no cover
        msg = "`get_context` is not used by Litestar's controller"
        raise ValueError(msg)

    async def get_root_value(
        self, request: Union[Request[Any, Any, Any], WebSocket]
    ) -> RootValue | None:  # pragma: no cover
        msg = "`get_root_value` is not used by Litestar's controller"
        raise ValueError(msg)

    async def get_sub_response(self, request: Request[Any, Any, Any]) -> Response:
        return self.temporal_response


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
    subscription_protocols: tuple[str, ...] = (
        GRAPHQL_TRANSPORT_WS_PROTOCOL,
        GRAPHQL_WS_PROTOCOL,
    ),
    connection_init_wait_timeout: timedelta = timedelta(minutes=1),
    multipart_uploads_enabled: bool = False,
) -> type[GraphQLController]:  # sourcery skip: move-assign
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
        dependencies: ClassVar[Dependencies] = {  # type: ignore[misc]
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
    _GraphQLController.multipart_uploads_enabled = multipart_uploads_enabled

    return _GraphQLController


__all__ = [
    "GraphQLController",
    "make_graphql_controller",
]
