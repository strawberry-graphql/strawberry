"""GraphQLHTTPHandler.

A consumer to provide a graphql endpoint, and optionally graphiql.
"""

from __future__ import annotations

import dataclasses
import json
import warnings
from functools import cached_property
from io import BytesIO
from typing import TYPE_CHECKING, Any, Dict, Mapping, Optional, Union
from urllib.parse import parse_qs

from django.conf import settings
from django.core.files import uploadhandler
from django.http.multipartparser import MultiPartParser

from channels.db import database_sync_to_async
from channels.generic.http import AsyncHttpConsumer
from strawberry.http.async_base_view import AsyncBaseHTTPView, AsyncHTTPRequestAdapter
from strawberry.http.exceptions import HTTPException
from strawberry.http.sync_base_view import SyncBaseHTTPView, SyncHTTPRequestAdapter
from strawberry.http.temporal_response import TemporalResponse
from strawberry.http.types import FormData
from strawberry.http.typevars import Context, RootValue
from strawberry.types.unset import UNSET

from .base import ChannelsConsumer

if TYPE_CHECKING:
    from strawberry.http import GraphQLHTTPResponse
    from strawberry.http.ides import GraphQL_IDE
    from strawberry.http.types import HTTPMethod, QueryParams
    from strawberry.schema import BaseSchema


@dataclasses.dataclass
class ChannelsResponse:
    content: bytes
    status: int = 200
    content_type: str = "application/json"
    headers: Dict[bytes, bytes] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class ChannelsRequest:
    consumer: ChannelsConsumer
    body: bytes

    @property
    def query_params(self) -> QueryParams:
        query_params_str = self.consumer.scope["query_string"].decode()

        query_params = {}
        for key, value in parse_qs(query_params_str, keep_blank_values=True).items():
            # Only one argument per key is expected here
            query_params[key] = value[0]

        return query_params

    @property
    def headers(self) -> Mapping[str, str]:
        return {
            header_name.decode().lower(): header_value.decode()
            for header_name, header_value in self.consumer.scope["headers"]
        }

    @property
    def method(self) -> HTTPMethod:
        return self.consumer.scope["method"].upper()

    @property
    def content_type(self) -> Optional[str]:
        return self.headers.get("content-type", None)

    @cached_property
    def form_data(self) -> FormData:
        upload_handlers = [
            uploadhandler.load_handler(handler)
            for handler in settings.FILE_UPLOAD_HANDLERS
        ]

        parser = MultiPartParser(
            {
                "CONTENT_TYPE": self.headers.get("content-type"),
                "CONTENT_LENGTH": self.headers.get("content-length", "0"),
            },
            BytesIO(self.body),
            upload_handlers,
        )

        querydict, files = parser.parse()

        form = {
            "operations": querydict.get("operations", "{}"),
            "map": querydict.get("map", "{}"),
        }

        return FormData(files=files, form=form)


class BaseChannelsRequestAdapter:
    def __init__(self, request: ChannelsRequest) -> None:
        self.request = request

    @property
    def query_params(self) -> QueryParams:
        return self.request.query_params

    @property
    def method(self) -> HTTPMethod:
        return self.request.method

    @property
    def headers(self) -> Mapping[str, str]:
        return self.request.headers

    @property
    def content_type(self) -> Optional[str]:
        return self.request.content_type


class ChannelsRequestAdapter(BaseChannelsRequestAdapter, AsyncHTTPRequestAdapter):
    async def get_body(self) -> bytes:
        return self.request.body

    async def get_form_data(self) -> FormData:
        return self.request.form_data


class SyncChannelsRequestAdapter(BaseChannelsRequestAdapter, SyncHTTPRequestAdapter):
    @property
    def body(self) -> bytes:
        return self.request.body

    @property
    def post_data(self) -> Mapping[str, Union[str, bytes]]:
        return self.request.form_data["form"]

    @property
    def files(self) -> Mapping[str, Any]:
        return self.request.form_data["files"]


class BaseGraphQLHTTPConsumer(ChannelsConsumer, AsyncHttpConsumer):
    graphql_ide_html: str
    graphql_ide: Optional[GraphQL_IDE] = "graphiql"

    def __init__(
        self,
        schema: BaseSchema,
        graphiql: Optional[bool] = None,
        graphql_ide: Optional[GraphQL_IDE] = "graphiql",
        allow_queries_via_get: bool = True,
        subscriptions_enabled: bool = True,
        **kwargs: Any,
    ) -> None:
        self.schema = schema
        self.allow_queries_via_get = allow_queries_via_get
        self.subscriptions_enabled = subscriptions_enabled
        self._ide_subscriptions_enabled = subscriptions_enabled

        if graphiql is not None:
            warnings.warn(
                "The `graphiql` argument is deprecated in favor of `graphql_ide`",
                DeprecationWarning,
                stacklevel=2,
            )
            self.graphql_ide = "graphiql" if graphiql else None
        else:
            self.graphql_ide = graphql_ide

        super().__init__(**kwargs)

    def create_response(
        self, response_data: GraphQLHTTPResponse, sub_response: TemporalResponse
    ) -> ChannelsResponse:
        return ChannelsResponse(
            content=json.dumps(response_data).encode(),
            status=sub_response.status_code,
            headers={k.encode(): v.encode() for k, v in sub_response.headers.items()},
        )

    async def handle(self, body: bytes) -> None:
        request = ChannelsRequest(consumer=self, body=body)
        try:
            response: ChannelsResponse = await self.run(request)

            if b"Content-Type" not in response.headers:
                response.headers[b"Content-Type"] = response.content_type.encode()

            await self.send_response(
                response.status,
                response.content,
                headers=response.headers,
            )
        except HTTPException as e:
            await self.send_response(e.status_code, e.reason.encode())


class GraphQLHTTPConsumer(
    BaseGraphQLHTTPConsumer,
    AsyncBaseHTTPView[
        ChannelsRequest,
        ChannelsResponse,
        TemporalResponse,
        Context,
        RootValue,
    ],
):
    """A consumer to provide a view for GraphQL over HTTP.

    To use this, place it in your ProtocolTypeRouter for your channels project:

    ```
    from strawberry.channels import GraphQLHttpRouter
    from channels.routing import ProtocolTypeRouter
    from django.core.asgi import get_asgi_application

    application = ProtocolTypeRouter({
        "http": URLRouter([
            re_path("^graphql", GraphQLHTTPRouter(schema=schema)),
            re_path("^", get_asgi_application()),
        ]),
        "websocket": URLRouter([
            re_path("^ws/graphql", GraphQLWebSocketRouter(schema=schema)),
        ]),
    })
    ```
    """

    allow_queries_via_get: bool = True
    request_adapter_class = ChannelsRequestAdapter

    async def get_root_value(self, request: ChannelsRequest) -> Optional[RootValue]:
        return None  # pragma: no cover

    async def get_context(
        self, request: ChannelsRequest, response: TemporalResponse
    ) -> Context:
        return {
            "request": request,
            "response": response,
        }  # type: ignore

    async def get_sub_response(self, request: ChannelsRequest) -> TemporalResponse:
        return TemporalResponse()

    async def render_graphql_ide(self, request: ChannelsRequest) -> ChannelsResponse:
        return ChannelsResponse(
            content=self.graphql_ide_html.encode(), content_type="text/html"
        )


class SyncGraphQLHTTPConsumer(
    BaseGraphQLHTTPConsumer,
    SyncBaseHTTPView[
        ChannelsRequest,
        ChannelsResponse,
        TemporalResponse,
        Context,
        RootValue,
    ],
):
    """Synchronous version of the HTTPConsumer.

    This is the same as `GraphQLHTTPConsumer`, but it can be used with
    synchronous schemas (i.e. the schema's resolvers are expected to be
    synchronous and not asynchronous).
    """

    allow_queries_via_get: bool = True
    request_adapter_class = SyncChannelsRequestAdapter

    def get_root_value(self, request: ChannelsRequest) -> Optional[RootValue]:
        return None  # pragma: no cover

    def get_context(
        self, request: ChannelsRequest, response: TemporalResponse
    ) -> Context:
        return {
            "request": request,
            "response": response,
        }  # type: ignore

    def get_sub_response(self, request: ChannelsRequest) -> TemporalResponse:
        return TemporalResponse()

    def render_graphql_ide(self, request: ChannelsRequest) -> ChannelsResponse:
        return ChannelsResponse(
            content=self.graphql_ide_html.encode(), content_type="text/html"
        )

    # Sync channels is actually async, but it uses database_sync_to_async to call
    # handlers in a threadpool. Check SyncConsumer's documentation for more info:
    # https://github.com/django/channels/blob/main/channels/consumer.py#L104
    @database_sync_to_async  # pyright: ignore[reportIncompatibleMethodOverride]
    def run(
        self,
        request: ChannelsRequest,
        context: Optional[Context] = UNSET,
        root_value: Optional[RootValue] = UNSET,
    ) -> ChannelsResponse:
        return super().run(request, context, root_value)


__all__ = ["GraphQLHTTPConsumer", "SyncGraphQLHTTPConsumer"]
