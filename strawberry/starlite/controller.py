"""Starlite integration for strawberry-graphql."""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING, Any, Dict, Mapping, Optional, Tuple, Union, cast
from typing_extensions import deprecated

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
from starlite.exceptions import (
    NotFoundException,
    ValidationException,
)
from starlite.status_codes import HTTP_200_OK
from strawberry.exceptions import InvalidCustomContext
from strawberry.http.async_base_view import AsyncBaseHTTPView, AsyncHTTPRequestAdapter
from strawberry.http.exceptions import HTTPException
from strawberry.http.types import FormData, HTTPMethod, QueryParams
from strawberry.http.typevars import (
    Context,
    RootValue,
)
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL
from strawberry.subscriptions.protocols.graphql_transport_ws import (
    WS_4406_PROTOCOL_NOT_ACCEPTABLE,
)

from .handlers.graphql_transport_ws_handler import (
    GraphQLTransportWSHandler as BaseGraphQLTransportWSHandler,
)
from .handlers.graphql_ws_handler import GraphQLWSHandler as BaseGraphQLWSHandler

if TYPE_CHECKING:
    from typing import FrozenSet, List, Type

    from starlite.types import AnyCallable, Dependencies
    from strawberry.http import GraphQLHTTPResponse
    from strawberry.http.ides import GraphQL_IDE
    from strawberry.schema import BaseSchema

    MergedContext = Union[
        "BaseContext",
        Union[
            Dict[str, Any],
            Dict[str, BackgroundTasks],
            Dict[str, Request[Any, Any]],
            Dict[str, Response[Any]],
            Dict[str, websocket],
        ],
    ]

CustomContext = Union["BaseContext", Dict[str, Any]]


async def _context_getter(
    custom_context: Optional[CustomContext],
    request: Request[Any, Any],
    response: Response[Any],
) -> MergedContext:
    if isinstance(custom_context, BaseContext):
        custom_context.request = request
        return custom_context

    default_context = {
        "request": request,
        "response": response,
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


@deprecated(
    "The `starlite` integration is deprecated in favor of `litestar` integration",
    stacklevel=2,
)
class StarliteRequestAdapter(AsyncHTTPRequestAdapter):
    def __init__(self, request: Request[Any, Any]) -> None:
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


class BaseContext:
    def __init__(self) -> None:
        self.request: Optional[Union[Request, WebSocket]] = None
        self.response: Optional[Response] = None


@deprecated(
    "The `starlite` integration is deprecated in favor of `litestar` integration",
    stacklevel=2,
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
) -> Type[Controller]:
    routes_path = path

    if context_getter is None:

        def custom_context_getter_() -> None:
            return None

    else:
        custom_context_getter_ = context_getter

    if root_value_getter is None:

        def root_value_getter_() -> None:
            return None

    else:
        root_value_getter_ = root_value_getter

    def response_getter() -> Response[Any]:
        return Response({}, background=BackgroundTasks([]))

    schema_ = schema
    allow_queries_via_get_ = allow_queries_via_get
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

    class GraphQLController(
        Controller,
        AsyncBaseHTTPView[
            Request[Any, Any], Response[Any], Response[Any], Context, RootValue
        ],
    ):
        request_adapter_class = StarliteRequestAdapter
        path: str = routes_path
        dependencies: Optional[Dependencies] = {
            "custom_context": Provide(custom_context_getter_),
            "context": Provide(_context_getter),
            "root_value": Provide(root_value_getter_),
            "response": Provide(response_getter),
        }
        graphql_ws_handler_class: Type[GraphQLWSHandler] = GraphQLWSHandler
        graphql_transport_ws_handler_class: Type[GraphQLTransportWSHandler] = (
            GraphQLTransportWSHandler
        )

        _keep_alive: bool = keep_alive
        _keep_alive_interval: float = keep_alive_interval
        _debug: bool = debug
        _protocols: Tuple[str, ...] = subscription_protocols
        _connection_init_wait_timeout: timedelta = connection_init_wait_timeout
        _graphiql_allowed_accept: FrozenSet[str] = frozenset({"text/html", "*/*"})

        schema: BaseSchema = schema_
        allow_queries_via_get = allow_queries_via_get_
        graphql_ide = graphql_ide_

        async def execute_request(
            self,
            request: Request[Any, Any],
            context: CustomContext,
            root_value: Any,
        ) -> Response[Union[GraphQLResource, str]]:
            try:
                return await self.run(
                    request,
                    # TODO: check the dependency, above, can we make it so that
                    # we don't need to type ignore here?
                    context=context,  # type: ignore
                    root_value=root_value,
                )
            except HTTPException as e:
                return Response(
                    e.reason,
                    status_code=e.status_code,
                    media_type=MediaType.TEXT,
                )

        async def render_graphql_ide(self, request: Request[Any, Any]) -> Response[str]:
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
            request: Request[Any, Any],
            context: CustomContext,
            root_value: Any,
            response: Response[Any],
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
            request: Request[Any, Any],
            context: CustomContext,
            root_value: Any,
            response: Response[Any],
        ) -> Response[Union[GraphQLResource, str]]:
            self.temporal_response = response

            return await self.execute_request(
                request=request,
                context=context,
                root_value=root_value,
            )

        async def get_context(
            self, request: Request[Any, Any], response: Response[Any]
        ) -> Context:  # pragma: no cover
            raise ValueError("`get_context` is not used by Starlite's controller")

        async def get_root_value(
            self, request: Request[Any, Any]
        ) -> Optional[RootValue]:  # pragma: no cover
            raise ValueError("`get_root_value` is not used by Starlite's controller")

        async def get_sub_response(self, request: Request[Any, Any]) -> Response[Any]:
            return self.temporal_response

        @websocket()
        async def websocket_endpoint(
            self,
            socket: WebSocket,
            context: CustomContext,
            root_value: Any,
        ) -> None:
            async def _get_context() -> CustomContext:
                return context

            async def _get_root_value() -> Any:
                return root_value

            preferred_protocol = self.pick_preferred_protocol(socket)
            if preferred_protocol == GRAPHQL_TRANSPORT_WS_PROTOCOL:
                await self.graphql_transport_ws_handler_class(
                    schema=self.schema,
                    debug=self._debug,
                    connection_init_wait_timeout=self._connection_init_wait_timeout,
                    get_context=_get_context,
                    get_root_value=_get_root_value,
                    ws=socket,
                ).handle()
            elif preferred_protocol == GRAPHQL_WS_PROTOCOL:
                await self.graphql_ws_handler_class(
                    schema=self.schema,
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


__all__ = ["make_graphql_controller"]
