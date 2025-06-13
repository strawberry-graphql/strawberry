from __future__ import annotations

import json
import warnings
from collections.abc import AsyncGenerator, Sequence
from datetime import timedelta
from json.decoder import JSONDecodeError
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Optional,
    Union,
    cast,
)
from typing_extensions import TypeGuard

from sanic import HTTPResponse, Request, Websocket, html
from sanic.views import HTTPMethodView
from strawberry.http.async_base_view import (
    AsyncBaseHTTPView,
    AsyncHTTPRequestAdapter,
    AsyncWebSocketAdapter,
)
from strawberry.http.exceptions import (
    HTTPException,
    NonJsonMessageReceived,
    NonTextMessageReceived,
)
from strawberry.http.temporal_response import TemporalResponse
from strawberry.http.types import FormData, HTTPMethod, QueryParams
from strawberry.http.typevars import (
    Context,
    RootValue,
)
from strawberry.sanic.utils import convert_request_to_files_dict
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Mapping

    from strawberry.http import GraphQLHTTPResponse
    from strawberry.http.ides import GraphQL_IDE
    from strawberry.schema import BaseSchema


class SanicHTTPRequestAdapter(AsyncHTTPRequestAdapter):
    def __init__(self, request: Request) -> None:
        self.request = request

    @property
    def query_params(self) -> QueryParams:
        # Just a heads up, Sanic's request.args uses urllib.parse.parse_qs
        # to parse query string parameters. This returns a dictionary where
        # the keys are the unique variable names and the values are lists
        # of values for each variable name. To ensure consistency, we're
        # enforcing the use of the first value in each list.
        args = self.request.get_args(keep_blank_values=True)
        return {k: args.get(k, None) for k in args}

    @property
    def method(self) -> HTTPMethod:
        return cast("HTTPMethod", self.request.method.upper())

    @property
    def headers(self) -> Mapping[str, str]:
        return self.request.headers

    @property
    def content_type(self) -> Optional[str]:
        return self.request.content_type

    async def get_body(self) -> str:
        return self.request.body.decode()

    async def get_form_data(self) -> FormData:
        assert self.request.form is not None

        files = convert_request_to_files_dict(self.request)

        return FormData(form=self.request.form, files=files)


class SanicWebSocketAdapter(AsyncWebSocketAdapter):
    def __init__(
        self, view: AsyncBaseHTTPView, request: Websocket, response: Websocket
    ) -> None:
        super().__init__(view)
        self.ws = request

    async def iter_json(
        self, *, ignore_parsing_errors: bool = False
    ) -> AsyncGenerator[object, None]:
        async for message in self.ws:
            if not isinstance(message, str):
                raise NonTextMessageReceived

            try:
                yield self.view.decode_json(message)
            except JSONDecodeError as e:
                if not ignore_parsing_errors:
                    raise NonJsonMessageReceived from e

    async def send_json(self, message: Mapping[str, object]) -> None:
        await self.ws.send(self.view.encode_json(message))

    async def close(self, code: int, reason: str) -> None:
        await self.ws.close(code, reason)


class GraphQLView(
    AsyncBaseHTTPView[
        Request,
        HTTPResponse,
        TemporalResponse,
        Websocket,
        Websocket,
        Context,
        RootValue,
    ],
    HTTPMethodView,
):
    """Class based view to handle GraphQL HTTP Requests.

    Args:
        schema: strawberry.Schema
        graphiql: bool, default is True
        allow_queries_via_get: bool, default is True

    Returns:
        None

    Example:
        app.add_route(
            GraphQLView.as_view(schema=schema, graphiql=True),
            "/graphql"
        )
    """

    allow_queries_via_get = True
    request_adapter_class = SanicHTTPRequestAdapter
    websocket_adapter_class = SanicWebSocketAdapter

    def __init__(
        self,
        schema: BaseSchema,
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
        json_encoder: Optional[type[json.JSONEncoder]] = None,
        json_dumps_params: Optional[dict[str, Any]] = None,
        multipart_uploads_enabled: bool = False,
    ) -> None:
        self.schema = schema
        self.allow_queries_via_get = allow_queries_via_get
        self.keep_alive = keep_alive
        self.keep_alive_interval = keep_alive_interval
        self.debug = debug
        self.protocols = subscription_protocols
        self.connection_init_wait_timeout = connection_init_wait_timeout
        self.json_encoder = json_encoder
        self.json_dumps_params = json_dumps_params
        self.multipart_uploads_enabled = multipart_uploads_enabled

        if self.json_encoder is not None:  # pragma: no cover
            warnings.warn(
                "json_encoder is deprecated, override encode_json instead",
                DeprecationWarning,
                stacklevel=2,
            )

        if self.json_dumps_params is not None:  # pragma: no cover
            warnings.warn(
                "json_dumps_params is deprecated, override encode_json instead",
                DeprecationWarning,
                stacklevel=2,
            )

            self.json_encoder = json.JSONEncoder

        if graphiql is not None:
            warnings.warn(
                "The `graphiql` argument is deprecated in favor of `graphql_ide`",
                DeprecationWarning,
                stacklevel=2,
            )
            self.graphql_ide = "graphiql" if graphiql else None
        else:
            self.graphql_ide = graphql_ide

    async def get_root_value(
        self, request: Union[Request, Websocket]
    ) -> Optional[RootValue]:
        return None

    async def get_context(
        self,
        request: Union[Request, Websocket],
        response: Union[TemporalResponse, Websocket],
    ) -> Context:
        return {"request": request, "response": response}  # type: ignore

    async def render_graphql_ide(self, request: Request) -> HTTPResponse:
        return html(self.graphql_ide_html)

    async def get_sub_response(self, request: Request) -> TemporalResponse:
        return TemporalResponse()

    def create_response(
        self, response_data: GraphQLHTTPResponse, sub_response: TemporalResponse
    ) -> HTTPResponse:
        status_code = sub_response.status_code

        data = self.encode_json(response_data)

        return HTTPResponse(
            data,
            status=status_code,
            content_type="application/json",
            headers=sub_response.headers,
        )

    async def post(self, request: Request) -> HTTPResponse:
        self.request = request

        try:
            return await self.run(request)
        except HTTPException as e:
            return HTTPResponse(e.reason, status=e.status_code)

    async def get(self, request: Request) -> HTTPResponse:
        self.request = request

        try:
            return await self.run(request)
        except HTTPException as e:
            return HTTPResponse(e.reason, status=e.status_code)

    async def websocket(self, request: Request, ws: Websocket) -> Websocket:
        return await self.run(ws)

    async def create_streaming_response(
        self,
        request: Request,
        stream: Callable[[], AsyncGenerator[str, None]],
        sub_response: TemporalResponse,
        headers: dict[str, str],
    ) -> HTTPResponse:
        response = await self.request.respond(
            status=sub_response.status_code,
            headers={
                **sub_response.headers,
                **headers,
            },
        )

        async for chunk in stream():
            await response.send(chunk)

        await response.eof()

        # returning the response will basically tell sanic to send it again
        # to the client, so we return None to avoid that, and we ignore the type
        # error mostly so we don't have to update the types everywhere for this
        # corner case
        return None  # type: ignore

    def is_websocket_request(
        self, request: Union[Request, Websocket]
    ) -> TypeGuard[Websocket]:
        # TODO: sanic gives us a WebSocketConnection when ASGI is used, which has a completely different inferface???
        return isinstance(request, Websocket)

    async def pick_websocket_subprotocol(self, request: Websocket) -> Optional[str]:
        return None

    async def create_websocket_response(
        self, request: Websocket, subprotocol: Optional[str]
    ) -> Websocket:
        return request


__all__ = ["GraphQLView"]
