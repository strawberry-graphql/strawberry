import warnings
from collections.abc import AsyncGenerator, Mapping
from datetime import timedelta
from typing import TYPE_CHECKING, Callable, ClassVar, Optional, cast
from typing_extensions import TypeGuard
from json.decoder import JSONDecodeError

from quart import Quart, Request, Response, websocket, request
from quart.ctx import has_websocket_context
from quart.views import View
from strawberry.http.async_base_view import (
    AsyncBaseHTTPView,
    AsyncHTTPRequestAdapter,
    AsyncWebSocketAdapter
)
from strawberry.http.exceptions import (
    HTTPException,
    NonJsonMessageReceived,
    WebSocketDisconnected
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
        return cast(HTTPMethod, self.request.method.upper())

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
    def __init__(self, view: AsyncBaseHTTPView, request, ws) -> None:
        super().__init__(view)
        self.ws = websocket

    async def iter_json(
        self, *, ignore_parsing_errors: bool = False
    ) -> AsyncGenerator[object, None]:
        while True:
            try:
                message = await self.ws.receive()
                try:
                    yield self.view.decode_json(message)
                except JSONDecodeError as e:
                    if not ignore_parsing_errors:
                        raise NonJsonMessageReceived from e
            except Exception as exc:
                raise WebSocketDisconnected from exc

    async def send_json(self, message: Mapping[str, object]) -> None:
        try:
            await self.ws.send(self.view.encode_json(message))
        except Exception as exc:
            raise WebSocketDisconnected from exc

    async def close(self, code: int, reason: str) -> None:
        await self.ws.close(code, reason=reason)


class GraphQLView(
    AsyncBaseHTTPView[
        Request, Response, Response, Request, Response, Context, RootValue
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
        subscription_protocols: list[str] = [
            GRAPHQL_TRANSPORT_WS_PROTOCOL,
            GRAPHQL_WS_PROTOCOL,
        ],
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

    async def get_context(self, request: Request, response: Response) -> Context:
        return {"request": request, "response": response}  # type: ignore

    async def get_root_value(self, request: Request) -> Optional[RootValue]:
        return None

    async def get_sub_response(self, request: Request) -> Response:
        return Response(status=200, content_type="application/json")

    async def dispatch_request(self) -> "ResponseReturnValue":  # type: ignore
        try:
            return await self.run(request=request)
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

    def is_websocket_request(self, request: Request) -> TypeGuard[Request]:
        if has_websocket_context():
            return True

        # Check if the request is a WebSocket upgrade request
        connection = request.headers.get("Connection", "").lower()
        upgrade = request.headers.get("Upgrade", "").lower()

        return ("upgrade" in connection and "websocket" in upgrade)

    async def pick_websocket_subprotocol(self, request: Request) -> Optional[str]:
        # Get the requested protocols
        protocols_header = websocket.headers.get("Sec-WebSocket-Protocol", "")
        if not protocols_header:
            return None

        # Find the first matching protocol
        requested_protocols = [p.strip() for p in protocols_header.split(",")]
        for protocol in requested_protocols:
            if protocol in self.subscription_protocols:
                return protocol

        return None

    async def create_websocket_response(
        self, request: Request, subprotocol: Optional[str]
    ) -> Response:
        if subprotocol:
            # Set the WebSocket protocol if specified
            await websocket.accept(subprotocol=subprotocol)
        else:
            await websocket.accept()

        # Return the current websocket context as the "response"
        return None

    @classmethod
    def register_route(cls, app: Quart, rule_name: str, path: str, **kwargs):
        """
        Helper method to register both HTTP and WebSocket handlers for a given path.

        Args:
            app: The Quart application
            rule_name: The name of the rule
            path: The path to register the handlers for
            **kwargs: Parameters to pass to the GraphQLView constructor
        """
        # Register both HTTP and WebSocket handler at the same path
        view_func = cls.as_view(rule_name, **kwargs)
        app.add_url_rule(path, view_func=view_func, methods=["GET", "POST"])

        # Register the WebSocket handler using the same view function
        # Quart will handle routing based on the WebSocket upgrade header
        app.add_url_rule(path, view_func=view_func, methods=["GET"], websocket=True)


__all__ = ["GraphQLView"]
