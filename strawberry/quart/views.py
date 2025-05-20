import asyncio
import warnings
from collections.abc import AsyncGenerator, Mapping, Sequence
from datetime import timedelta
from json.decoder import JSONDecodeError
from typing import TYPE_CHECKING, Callable, ClassVar, Optional, Union, cast
from typing_extensions import TypeGuard

from quart import Request, Response, Websocket, request, websocket
from quart.ctx import has_websocket_context
from quart.views import View
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
from strawberry.http.ides import GraphQL_IDE
from strawberry.http.types import FormData, HTTPMethod, QueryParams
from strawberry.http.typevars import Context, RootValue
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL

if TYPE_CHECKING:
    from quart.typing import ResponseReturnValue
    from strawberry.http import GraphQLHTTPResponse
    from strawberry.schema.base import BaseSchema


class QuartHTTPRequestAdapter(AsyncHTTPRequestAdapter):
    def __init__(self, request: Request) -> None:
        self.request = request

    @property
    def query_params(self) -> QueryParams:
        return self.request.args.to_dict()

    @property
    def method(self) -> HTTPMethod:
        return cast("HTTPMethod", self.request.method.upper())

    @property
    def content_type(self) -> Optional[str]:
        return self.request.content_type

    @property
    def headers(self) -> Mapping[str, str]:
        return self.request.headers  # type: ignore

    async def get_body(self) -> str:
        return (await self.request.data).decode()

    async def get_form_data(self) -> FormData:
        files = await self.request.files
        form = await self.request.form
        return FormData(files=files, form=form)


class QuartWebSocketAdapter(AsyncWebSocketAdapter):
    def __init__(
        self, view: AsyncBaseHTTPView, request: Websocket, response: Response
    ) -> None:
        super().__init__(view)
        self.ws = request

    async def iter_json(
        self, *, ignore_parsing_errors: bool = False
    ) -> AsyncGenerator[object, None]:
        try:
            while True:
                # Raises asyncio.CancelledError when the connection is closed.
                # https://quart.palletsprojects.com/en/latest/how_to_guides/websockets.html#detecting-disconnection
                message = await self.ws.receive()

                if not isinstance(message, str):
                    raise NonTextMessageReceived

                try:
                    yield self.view.decode_json(message)
                except JSONDecodeError as e:
                    if not ignore_parsing_errors:
                        raise NonJsonMessageReceived from e
        except asyncio.CancelledError:
            pass

    async def send_json(self, message: Mapping[str, object]) -> None:
        try:
            # Raises asyncio.CancelledError when the connection is closed.
            # https://quart.palletsprojects.com/en/latest/how_to_guides/websockets.html#detecting-disconnection
            await self.ws.send(self.view.encode_json(message))
        except asyncio.CancelledError as exc:
            raise WebSocketDisconnected from exc

    async def close(self, code: int, reason: str) -> None:
        await self.ws.close(code, reason=reason)


class GraphQLView(
    AsyncBaseHTTPView[
        Request, Response, Response, Websocket, Response, Context, RootValue
    ],
    View,
):
    methods: ClassVar[list[str]] = ["GET", "POST"]
    allow_queries_via_get: bool = True
    request_adapter_class = QuartHTTPRequestAdapter
    websocket_adapter_class = QuartWebSocketAdapter

    def __init__(
        self,
        schema: "BaseSchema",
        graphiql: Optional[bool] = None,
        graphql_ide: Optional[GraphQL_IDE] = "graphiql",
        allow_queries_via_get: bool = True,
        keep_alive: bool = True,
        keep_alive_interval: float = 1,
        debug: bool = False,
        subscription_protocols: Sequence[str] = (
            GRAPHQL_TRANSPORT_WS_PROTOCOL,
            GRAPHQL_WS_PROTOCOL,
        ),
        connection_init_wait_timeout: timedelta = timedelta(minutes=1),
        multipart_uploads_enabled: bool = False,
    ) -> None:
        self.schema = schema
        self.allow_queries_via_get = allow_queries_via_get
        self.keep_alive = keep_alive
        self.keep_alive_interval = keep_alive_interval
        self.debug = debug
        self.subscription_protocols = subscription_protocols
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

    async def render_graphql_ide(self, request: Request) -> Response:
        return Response(self.graphql_ide_html)

    def create_response(
        self, response_data: "GraphQLHTTPResponse", sub_response: Response
    ) -> Response:
        sub_response.set_data(self.encode_json(response_data))

        return sub_response

    async def get_context(
        self, request: Union[Request, Websocket], response: Response
    ) -> Context:
        return {"request": request, "response": response}  # type: ignore

    async def get_root_value(
        self, request: Union[Request, Websocket]
    ) -> Optional[RootValue]:
        return None

    async def get_sub_response(self, request: Request) -> Response:
        return Response(status=200, content_type="application/json")

    async def dispatch_request(self, **kwargs: object) -> "ResponseReturnValue":
        try:
            return await self.run(
                request=websocket if has_websocket_context() else request
            )
        except HTTPException as e:
            return Response(
                response=e.reason,
                status=e.status_code,
            )

    async def create_streaming_response(
        self,
        request: Request,
        stream: Callable[[], AsyncGenerator[str, None]],
        sub_response: Response,
        headers: dict[str, str],
    ) -> Response:
        return (
            stream(),
            sub_response.status_code,
            {  # type: ignore
                **sub_response.headers,
                **headers,
            },
        )

    def is_websocket_request(
        self, request: Union[Request, Websocket]
    ) -> TypeGuard[Websocket]:
        return has_websocket_context()

    async def pick_websocket_subprotocol(self, request: Websocket) -> Optional[str]:
        protocols = request.requested_subprotocols
        intersection = set(protocols) & set(self.subscription_protocols)
        sorted_intersection = sorted(intersection, key=protocols.index)
        return next(iter(sorted_intersection), None)

    async def create_websocket_response(
        self, request: Websocket, subprotocol: Optional[str]
    ) -> Response:
        await request.accept(subprotocol=subprotocol)
        return Response()


__all__ = ["GraphQLView"]
