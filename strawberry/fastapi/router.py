from __future__ import annotations

import warnings
from datetime import timedelta
from inspect import signature
from typing import (
    TYPE_CHECKING,
    Any,
    TypeGuard,
    cast,
)

from cross_web import HTTPException, StarletteRequestAdapter
from fastapi import APIRouter, Depends, params
from fastapi.datastructures import Default
from fastapi.routing import APIRoute
from fastapi.utils import generate_unique_id
from starlette import status
from starlette.background import BackgroundTasks  # noqa: TC002
from starlette.requests import HTTPConnection, Request
from starlette.responses import (
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    Response,
    StreamingResponse,
)
from starlette.websockets import WebSocket

from strawberry.asgi import ASGIWebSocketAdapter
from strawberry.exceptions import InvalidCustomContext
from strawberry.fastapi.context import BaseContext, CustomContext
from strawberry.http.async_base_view import AsyncBaseHTTPView
from strawberry.http.typevars import Context, RootValue
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL

if TYPE_CHECKING:
    from collections.abc import (
        AsyncIterator,
        Awaitable,
        Callable,
        Sequence,
    )
    from enum import Enum

    from starlette.routing import BaseRoute
    from starlette.types import ASGIApp, Lifespan

    from strawberry.fastapi.context import MergedContext
    from strawberry.http import GraphQLHTTPResponse
    from strawberry.http.ides import GraphQL_IDE
    from strawberry.schema import BaseSchema


class GraphQLRouter(
    AsyncBaseHTTPView[
        Request, Response, Response, WebSocket, WebSocket, Context, RootValue
    ],
    APIRouter,
):
    allow_queries_via_get = True
    request_adapter_class = StarletteRequestAdapter
    websocket_adapter_class = ASGIWebSocketAdapter  # type: ignore

    @staticmethod
    async def __get_root_value() -> None:
        return None

    @staticmethod
    def __get_context_getter(
        custom_getter: Callable[
            ..., CustomContext | None | Awaitable[CustomContext | None]
        ],
    ) -> Callable[..., Awaitable[CustomContext]]:
        async def dependency(
            custom_context: CustomContext | None,
            background_tasks: BackgroundTasks,
            connection: HTTPConnection,
            response: Response = None,  # type: ignore
        ) -> MergedContext:
            request = cast("Request | WebSocket", connection)
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
            if custom_context is None:
                return default_context
            raise InvalidCustomContext

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
        graphiql: bool | None = None,
        graphql_ide: GraphQL_IDE | None = "graphiql",
        allow_queries_via_get: bool = True,
        keep_alive: bool = False,
        keep_alive_interval: float = 1,
        root_value_getter: Callable[[], RootValue] | None = None,
        context_getter: Callable[..., Context | None | Awaitable[Context | None]]
        | None = None,
        subscription_protocols: Sequence[str] = (
            GRAPHQL_TRANSPORT_WS_PROTOCOL,
            GRAPHQL_WS_PROTOCOL,
        ),
        connection_init_wait_timeout: timedelta = timedelta(minutes=1),
        prefix: str = "",
        tags: list[str | Enum] | None = None,
        dependencies: Sequence[params.Depends] | None = None,
        default_response_class: type[Response] = Default(JSONResponse),
        responses: dict[int | str, dict[str, Any]] | None = None,
        callbacks: list[BaseRoute] | None = None,
        routes: list[BaseRoute] | None = None,
        redirect_slashes: bool = True,
        default: ASGIApp | None = None,
        dependency_overrides_provider: Any | None = None,
        route_class: type[APIRoute] = APIRoute,
        on_startup: Sequence[Callable[[], Any]] | None = None,
        on_shutdown: Sequence[Callable[[], Any]] | None = None,
        lifespan: Lifespan[Any] | None = None,
        deprecated: bool | None = None,
        include_in_schema: bool = True,
        generate_unique_id_function: Callable[[APIRoute], str] = Default(
            generate_unique_id
        ),
        multipart_uploads_enabled: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            prefix=prefix,
            tags=tags,
            dependencies=dependencies,
            default_response_class=default_response_class,
            responses=responses,
            callbacks=callbacks,
            routes=routes,
            redirect_slashes=redirect_slashes,
            default=default,
            dependency_overrides_provider=dependency_overrides_provider,
            route_class=route_class,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            lifespan=lifespan,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            generate_unique_id_function=generate_unique_id_function,
            **kwargs,
        )
        self.schema = schema
        self.allow_queries_via_get = allow_queries_via_get
        self.keep_alive = keep_alive
        self.keep_alive_interval = keep_alive_interval
        self.root_value_getter = root_value_getter or self.__get_root_value
        # TODO: clean this type up
        self.context_getter = self.__get_context_getter(
            context_getter or (lambda: None)  # type: ignore
        )
        self.protocols = subscription_protocols
        self.connection_init_wait_timeout = connection_init_wait_timeout
        self.multipart_uploads_enabled = multipart_uploads_enabled

        if graphiql is not None:
            warnings.warn(
                "The `graphiql` argument is deprecated in favor of `graphql_ide`",
                DeprecationWarning,
                stacklevel=2,
            )
            self.graphql_ide = "graphiql" if graphiql else None
        else:
            self.graphql_ide = graphql_ide

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
        ) -> None:
            await self.run(request=websocket, context=context, root_value=root_value)

    async def render_graphql_ide(self, request: Request) -> HTMLResponse:
        return HTMLResponse(self.graphql_ide_html)

    async def get_context(
        self, request: Request | WebSocket, response: Response | WebSocket
    ) -> Context:  # pragma: no cover
        raise ValueError("`get_context` is not used by FastAPI GraphQL Router")

    async def get_root_value(
        self, request: Request | WebSocket
    ) -> RootValue | None:  # pragma: no cover
        raise ValueError("`get_root_value` is not used by FastAPI GraphQL Router")

    async def get_sub_response(self, request: Request) -> Response:
        return self.temporal_response

    def create_response(
        self,
        response_data: GraphQLHTTPResponse | list[GraphQLHTTPResponse],
        sub_response: Response,
    ) -> Response:
        response = Response(
            self.encode_json(response_data),
            media_type="application/json",
            status_code=sub_response.status_code or status.HTTP_200_OK,
        )

        response.headers.raw.extend(sub_response.headers.raw)

        return response

    async def create_streaming_response(
        self,
        request: Request,
        stream: Callable[[], AsyncIterator[str]],
        sub_response: Response,
        headers: dict[str, str],
    ) -> Response:
        return StreamingResponse(
            stream(),
            status_code=sub_response.status_code or status.HTTP_200_OK,
            headers={
                **sub_response.headers,
                **headers,
            },
        )

    def is_websocket_request(
        self, request: Request | WebSocket
    ) -> TypeGuard[WebSocket]:
        return request.scope["type"] == "websocket"

    async def pick_websocket_subprotocol(self, request: WebSocket) -> str | None:
        protocols = request["subprotocols"]
        intersection = set(protocols) & set(self.protocols)
        sorted_intersection = sorted(intersection, key=protocols.index)
        return next(iter(sorted_intersection), None)

    async def create_websocket_response(
        self, request: WebSocket, subprotocol: str | None
    ) -> WebSocket:
        await request.accept(subprotocol=subprotocol)
        return request


__all__ = ["GraphQLRouter"]
