from __future__ import annotations

from datetime import timedelta
from inspect import signature
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Mapping,
    Optional,
    Sequence,
    Union,
    cast,
)

from starlette import status
from starlette.background import BackgroundTasks  # noqa: TCH002
from starlette.requests import HTTPConnection, Request
from starlette.responses import (
    HTMLResponse,
    PlainTextResponse,
    Response,
)
from starlette.websockets import WebSocket

from fastapi import APIRouter, Depends
from strawberry.exceptions import InvalidCustomContext
from strawberry.fastapi.context import BaseContext, CustomContext
from strawberry.fastapi.handlers import GraphQLTransportWSHandler, GraphQLWSHandler
from strawberry.http import (
    process_result,
)
from strawberry.http.async_base_view import AsyncBaseHTTPView, AsyncHTTPRequestAdapter
from strawberry.http.exceptions import HTTPException
from strawberry.http.types import FormData, HTTPMethod, QueryParams
from strawberry.http.typevars import (
    Context,
    RootValue,
)
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL
from strawberry.utils.graphiql import get_graphiql_html

if TYPE_CHECKING:
    from starlette.types import ASGIApp

    from strawberry.fastapi.context import MergedContext
    from strawberry.http import GraphQLHTTPResponse
    from strawberry.schema import BaseSchema
    from strawberry.types import ExecutionResult


class FastAPIRequestAdapter(AsyncHTTPRequestAdapter):
    def __init__(self, request: Request):
        self.request = request

    @property
    def query_params(self) -> QueryParams:
        return dict(self.request.query_params)

    @property
    def method(self) -> HTTPMethod:
        return cast(HTTPMethod, self.request.method.upper())

    @property
    def headers(self) -> Mapping[str, str]:
        return self.request.headers

    @property
    def content_type(self) -> Optional[str]:
        return self.request.headers.get("Content-Type", None)

    async def get_body(self) -> bytes:
        return await self.request.body()

    async def get_form_data(self) -> FormData:
        multipart_data = await self.request.form()

        return FormData(files=multipart_data, form=multipart_data)


class GraphQLRouter(
    AsyncBaseHTTPView[Request, Response, Response, Context, RootValue], APIRouter
):
    graphql_ws_handler_class = GraphQLWSHandler
    graphql_transport_ws_handler_class = GraphQLTransportWSHandler
    allow_queries_via_get = True
    request_adapter_class = FastAPIRequestAdapter

    @staticmethod
    async def __get_root_value():
        return None

    @staticmethod
    def __get_context_getter(
        custom_getter: Callable[
            ..., Union[Optional[CustomContext], Awaitable[Optional[CustomContext]]]
        ]
    ) -> Callable[..., Awaitable[CustomContext]]:
        async def dependency(
            custom_context: Optional[CustomContext],
            background_tasks: BackgroundTasks,
            connection: HTTPConnection,
            response: Response = None,  # type: ignore
        ) -> MergedContext:
            request = cast(Union[Request, WebSocket], connection)
            if isinstance(custom_context, BaseContext):
                custom_context.request = request
                custom_context.background_tasks = background_tasks
                custom_context.response = response
                return custom_context
            default_context = {
                "request": request,
                "background_tasks": background_tasks,
                "response": response,
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

        # replace the signature parameters of dependency...
        # ...with the old parameters minus the first argument as it will be replaced...
        # ...with the value obtained by injecting custom_getter context as a dependency.
        sig = signature(dependency)
        sig = sig.replace(
            parameters=[
                *list(sig.parameters.values())[1:],
                sig.parameters["custom_context"].replace(
                    default=Depends(custom_getter)
                ),
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
        allow_queries_via_get: bool = True,
        keep_alive: bool = False,
        keep_alive_interval: float = 1,
        debug: bool = False,
        root_value_getter: Optional[Callable[[], RootValue]] = None,
        context_getter: Optional[Callable[..., Optional[Context]]] = None,
        subscription_protocols: Sequence[str] = (
            GRAPHQL_TRANSPORT_WS_PROTOCOL,
            GRAPHQL_WS_PROTOCOL,
        ),
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
        self.allow_queries_via_get = allow_queries_via_get
        self.keep_alive = keep_alive
        self.keep_alive_interval = keep_alive_interval
        self.debug = debug
        self.root_value_getter = root_value_getter or self.__get_root_value
        # TODO: clean this type up
        self.context_getter = self.__get_context_getter(
            context_getter or (lambda: None)  # type: ignore
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
                    "description": (
                        "Not found if GraphiQL or query via GET are not enabled."
                    )
                },
            },
            include_in_schema=graphiql or allow_queries_via_get,
        )
        async def handle_http_get(  # pyright: ignore
            request: Request,
            response: Response,
            context: Context = Depends(self.context_getter),
            root_value: RootValue = Depends(self.root_value_getter),
        ) -> Response:
            self.temporal_response = response

            try:
                return await self.run(
                    request=request, context=context, root_value=root_value
                )
            except HTTPException as e:
                return PlainTextResponse(
                    e.reason,
                    status_code=e.status_code,
                )

        @self.post(path)
        async def handle_http_post(  # pyright: ignore
            request: Request,
            response: Response,
            # TODO: use Annotated in future
            context: Context = Depends(self.context_getter),
            root_value: RootValue = Depends(self.root_value_getter),
        ) -> Response:
            self.temporal_response = response

            try:
                return await self.run(
                    request=request, context=context, root_value=root_value
                )
            except HTTPException as e:
                return PlainTextResponse(
                    e.reason,
                    status_code=e.status_code,
                )

        @self.websocket(path)
        async def websocket_endpoint(  # pyright: ignore
            websocket: WebSocket,
            context: Context = Depends(self.context_getter),
            root_value: RootValue = Depends(self.root_value_getter),
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
            key=lambda i: protocols.index(i),
            default=None,
        )

    def render_graphiql(self, request: Request) -> HTMLResponse:
        return HTMLResponse(get_graphiql_html())

    async def process_result(
        self, request: Request, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        return process_result(result)

    async def get_context(
        self, request: Request, response: Response
    ) -> Context:  # pragma: no cover
        raise ValueError("`get_context` is not used by FastAPI GraphQL Router")

    async def get_root_value(
        self, request: Request
    ) -> Optional[RootValue]:  # pragma: no cover
        raise ValueError("`get_root_value` is not used by FastAPI GraphQL Router")

    async def get_sub_response(self, request: Request) -> Response:
        return self.temporal_response

    def create_response(
        self, response_data: GraphQLHTTPResponse, sub_response: Response
    ) -> Response:
        response = Response(
            self.encode_json(response_data),
            media_type="application/json",
            status_code=sub_response.status_code or status.HTTP_200_OK,
        )

        response.headers.raw.extend(sub_response.headers.raw)

        return response
