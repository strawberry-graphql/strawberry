"""GraphQLHTTPHandler

A consumer to provide a graphql endpoint, and optionally graphiql.
"""

import dataclasses
import json
from pathlib import Path
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

from .base import ChannelsConsumer


class MethodNotAllowed(Exception):
    ...


class ExecutionError(Exception):
    ...


@dataclasses.dataclass
class Result:
    response: Any
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

    graphiql_html_file_path = (
        Path(__file__).parent.parent.parent / "static" / "graphiql.html"
    )

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
                headers=[b"Allow", b"GET, POST"],
            )
        except ExecutionError as e:
            await self.send_response(
                500,
                str(e).encode(),
            )
        else:
            await self.send_response(
                result.status,
                json.dumps(result.response).encode(),
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
            if "query" not in params:
                raise ExecutionError("No GraphQL query found in the request")

            try:
                return Result(response=await self.execute(parse_request_data(params)))
            except InvalidOperationTypeError as e:
                error_str = e.as_http_error_reason(self.scope["method"])
                raise ExecutionError(error_str) from e
        else:
            raise MethodNotAllowed()

    async def post(self, body: bytes) -> Result:
        request_data = await self.parse_body(body)
        try:
            return Result(response=await self.execute(request_data))
        except InvalidOperationTypeError as e:
            raise ExecutionError(e.as_http_error_reason(self.scope["method"])) from e

    async def parse_body(self, body: bytes) -> GraphQLRequestData:
        if self.headers.get("content-type", "").startswith("multipart/form-data"):
            return await self.parse_multipart_body(body)

        try:
            data = json.loads(body)
        except json.JSONDecodeError as e:
            raise ExecutionError("Unable to parse request body as JSON") from e

        try:
            return parse_request_data(data)
        except MissingQueryError as e:
            raise ExecutionError("No GraphQL query found in the request") from e

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
        html_string = self.graphiql_html_file_path.read_text()
        html_string = html_string.replace(
            "{{ SUBSCRIPTION_ENABLED }}",
            json.dumps(self.subscriptions_enabled),
        )
        return Result(response=html_string, content_type="text/html")

    def should_render_graphiql(self):
        return self.graphiql and self.headers.get("accept", "") in ["text/html", "*/*"]


class SyncGraphQLHTTPConsumer(GraphQLHTTPConsumer):
    """Synchronous version of the HTTPConsumer.

    This is the same as `GraphQLHTTPConsumer`, but it can be used with
    synchronous schemas (i.e. the schema's resolvers are espected to be
    synchronous and not asynchronous).
    """

    def get_root_value(self, request: Optional["ChannelsConsumer"] = None) -> Any:
        return None

    def get_context(
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
