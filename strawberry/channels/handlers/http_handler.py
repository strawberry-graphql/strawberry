"""GraphQLHTTPHandler

A consumer to provide a graphql endpoint, and optionally graphiql.
"""

import json
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qs

from backports.cached_property import cached_property

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


class GraphQLHTTPConsumer(AsyncHttpConsumer):
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

    @cached_property
    def headers(self):
        return {
            header_name.decode("utf-8").lower(): header_value.decode("utf-8")
            for header_name, header_value in self.scope["headers"]
        }

    async def parse_multipart_body(self, body):
        await self.send_response(500, "Unable to parse the multipart body")
        return None

    async def get_request_data(self, body) -> Optional[GraphQLRequestData]:
        if self.headers.get("content-type", "").startswith("multipart/form-data"):
            data = await self.parse_multipart_body(body)
            if data is None:
                return None
        else:
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                await self.send_response(500, b"Unable to parse request body as JSON")
                return None
        try:
            return parse_request_data(data)
        except MissingQueryError:
            await self.send_response(500, b"No GraphQL query found in the request")
            return None

    async def post(self, body):
        request_data = await self.get_request_data(body)
        if request_data is None:
            return None

        try:
            response = await self.execute(request_data)
        except InvalidOperationTypeError as e:
            await self.send_response(
                500, str(e.as_http_error_reason(self.scope["method"])).encode()
            )
            return None

        await self.send_response(
            200,
            json.dumps(response).encode("utf-8"),
            headers=[(b"Content-Type", b"application/json")],
        )

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

    @cached_property
    def graphiql_html_file_path(self) -> Path:
        return Path(__file__).parent.parent.parent / "static" / "graphiql.html"

    async def render_graphiql(self, body):
        html_string = self.graphiql_html_file_path.read_text()
        html_string = html_string.replace(
            "{{ SUBSCRIPTION_ENABLED }}",
            json.dumps(self.subscriptions_enabled),
        )
        await self.send_response(
            200, html_string.encode("utf-8"), headers=[(b"Content-Type", b"text/html")]
        )

    def should_render_graphiql(self):
        return bool(
            self.graphiql and self.headers.get("accept", "") in ["text/html", "*/*"]
        )

    async def get(self, body):
        if self.should_render_graphiql():
            await self.render_graphiql(body)
        elif self.scope.get("query_string"):
            params = parse_query_params(
                {
                    k: v[0]
                    for k, v in parse_qs(self.scope["query_string"].decode()).items()
                }
            )

            if "query" not in params:
                await self.send_response(500, b"No GraphQL query found in the request")
                return

            request_data = parse_request_data(params)
            try:
                response = await self.execute(request_data)
            except InvalidOperationTypeError as e:
                await self.send_response(
                    500, str(e.as_http_error_reason(self.scope["method"])).encode()
                )
                return None

            await self.send_response(
                200,
                json.dumps(response).encode("utf-8"),
                headers=[(b"Content-Type", b"application/json")],
            )
        else:
            await self.send_response(
                405, b"Method not allowed", headers=[b"Allow", b"GET, POST"]
            )

    async def handle(self, body):
        if self.scope["method"] == "GET":
            return await self.get(body)
        if self.scope["method"] == "POST":
            return await self.post(body)
        await self.send_response(
            405, b"Method not allowed", headers=[b"Allow", b"GET, POST"]
        )

    async def get_root_value(self) -> Any:
        return None

    async def get_context(self) -> Any:
        return StrawberryChannelsContext(request=self)

    async def process_result(self, result: ExecutionResult) -> GraphQLHTTPResponse:
        return process_result(result)


class SyncGraphQLHTTPConsumer(GraphQLHTTPConsumer):
    """Synchronous version of the HTTPConsumer.

    This is the same as `GraphQLHTTPConsumer`, but it can be used with
    synchronous schemas (i.e. the schema's resolvers are espected to be
    synchronous and not asynchronous).
    """

    def get_root_value(self) -> Any:
        return None

    def get_context(self) -> Any:
        return StrawberryChannelsContext(request=self)

    def process_result(self, result: ExecutionResult) -> GraphQLHTTPResponse:
        return process_result(result)

    # Sync channels is actually async, but it uses database_sync_to_async to call
    # handlers in a threadpool. Check SyncConsumer's documentation for more info:
    # https://github.com/django/channels/blob/main/channels/consumer.py#L104
    @database_sync_to_async
    def execute(self, request_data: GraphQLRequestData):
        context = self.get_context()
        root_value = self.get_root_value()

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
