"""GraphQLHTTPHandler

A consumer to provide a graphql endpoint, and optionally graphiql.
"""

import dataclasses
import json
from typing import Any, Optional
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.http import AsyncHttpConsumer
from strawberry.channels.context import StrawberryChannelsContext
from strawberry.exceptions import MissingQueryError
from strawberry.http import (
    GraphQLHTTPResponse,
    GraphQLRequestData,
    parse_query_params,
    parse_request_data,
    process_result,
)
from strawberry.schema import BaseSchema
from strawberry.schema.exceptions import InvalidOperationTypeError
from strawberry.types import ExecutionResult
from strawberry.types.graphql import OperationType
from strawberry.utils.graphiql import get_graphiql_html

from .base import ChannelsConsumer


class MethodNotAllowed(Exception):
    ...


class ExecutionError(Exception):
    ...


@dataclasses.dataclass
class Result:
    response: bytes
    status: int = 200
    content_type: str = "application/json"


class GraphQLHTTPConsumer(ChannelsConsumer, AsyncHttpConsumer):
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

    def __init__(
        self,
        schema: BaseSchema,
        graphiql: bool = True,
        allow_queries_via_get: bool = True,
        subscriptions_enabled: bool = True,
        **kwargs,
    ):
        self.schema = schema
        self.graphiql = graphiql
        self.allow_queries_via_get = allow_queries_via_get
        self.subscriptions_enabled = subscriptions_enabled
        super().__init__(**kwargs)

    async def handle(self, body: bytes):
        try:
            if self.scope["method"] == "GET":
                result = await self.get(body)
            elif self.scope["method"] == "POST":
                result = await self.post(body)
            else:
                raise MethodNotAllowed()
        except MethodNotAllowed:
            await self.send_response(
                405,
                b"Method not allowed",
                headers=[(b"Allow", b"GET, POST")],
            )
        except InvalidOperationTypeError as e:
            error_str = e.as_http_error_reason(self.scope["method"])
            await self.send_response(
                406,
                error_str.encode(),
            )
        except ExecutionError as e:
            await self.send_response(
                500,
                str(e).encode(),
            )
        else:
            await self.send_response(
                result.status,
                result.response,
                headers=[(b"Content-Type", result.content_type.encode())],
            )

    async def get(self, body: bytes) -> Result:
        if self.should_render_graphiql():
            return await self.render_graphiql(body)
        elif self.scope.get("query_string"):
            params = parse_query_params(
                {
                    k: v[0]
                    for k, v in parse_qs(self.scope["query_string"].decode()).items()
                }
            )

            try:
                result = await self.execute(parse_request_data(params))
            except MissingQueryError as e:
                raise ExecutionError("No GraphQL query found in the request") from e

            return Result(response=json.dumps(result).encode())
        else:
            raise MethodNotAllowed()

    async def post(self, body: bytes) -> Result:
        request_data = await self.parse_body(body)

        try:
            result = await self.execute(request_data)
        except MissingQueryError as e:
            raise ExecutionError("No GraphQL query found in the request") from e

        return Result(response=json.dumps(result).encode())

    async def parse_body(self, body: bytes) -> GraphQLRequestData:
        if self.headers.get("content-type", "").startswith("multipart/form-data"):
            return await self.parse_multipart_body(body)

        try:
            data = json.loads(body)
        except json.JSONDecodeError as e:
            raise ExecutionError("Unable to parse request body as JSON") from e

        return parse_request_data(data)

    async def parse_multipart_body(self, body: bytes) -> GraphQLRequestData:
        raise ExecutionError("Unable to parse the multipart body")

    async def execute(self, request_data: GraphQLRequestData):
        context = await self.get_context()
        root_value = await self.get_root_value()

        method = self.scope["method"]
        allowed_operation_types = OperationType.from_http(method)
        if not self.allow_queries_via_get and method == "GET":
            allowed_operation_types = allowed_operation_types - {OperationType.QUERY}

        result = await self.schema.execute(
            query=request_data.query,
            root_value=root_value,
            variable_values=request_data.variables,
            context_value=context,
            operation_name=request_data.operation_name,
            allowed_operation_types=allowed_operation_types,
        )
        return await self.process_result(result)

    async def process_result(self, result: ExecutionResult) -> GraphQLHTTPResponse:
        return process_result(result)

    async def render_graphiql(self, body):
        html = get_graphiql_html(self.subscriptions_enabled)
        return Result(response=html.encode(), content_type="text/html")

    def should_render_graphiql(self):
        accept_list = self.headers.get("accept", "").split(",")
        return self.graphiql and any(
            accepted in accept_list for accepted in ["text/html", "*/*"]
        )


class SyncGraphQLHTTPConsumer(GraphQLHTTPConsumer):
    """Synchronous version of the HTTPConsumer.

    This is the same as `GraphQLHTTPConsumer`, but it can be used with
    synchronous schemas (i.e. the schema's resolvers are espected to be
    synchronous and not asynchronous).
    """

    def get_root_value(self, request: Optional["ChannelsConsumer"] = None) -> Any:
        return None

    def get_context(  # type: ignore[override]
        self,
        request: Optional["ChannelsConsumer"] = None,
    ) -> StrawberryChannelsContext:
        return StrawberryChannelsContext(request=request or self)

    def process_result(  # type:ignore [override]
        self, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        return process_result(result)

    # Sync channels is actually async, but it uses database_sync_to_async to call
    # handlers in a threadpool. Check SyncConsumer's documentation for more info:
    # https://github.com/django/channels/blob/main/channels/consumer.py#L104
    @database_sync_to_async
    def execute(self, request_data: GraphQLRequestData):
        context = self.get_context(self)
        root_value = self.get_root_value(self)

        method = self.scope["method"]
        allowed_operation_types = OperationType.from_http(method)
        if not self.allow_queries_via_get and method == "GET":
            allowed_operation_types = allowed_operation_types - {OperationType.QUERY}

        result = self.schema.execute_sync(
            query=request_data.query,
            root_value=root_value,
            variable_values=request_data.variables,
            context_value=context,
            operation_name=request_data.operation_name,
            allowed_operation_types=allowed_operation_types,
        )
        return self.process_result(result)
