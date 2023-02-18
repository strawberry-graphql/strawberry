from __future__ import annotations

import json
from io import BytesIO
from typing import TYPE_CHECKING, Any, Dict, Union

from aiohttp import web
from strawberry.exceptions import MissingQueryError
from strawberry.file_uploads.utils import replace_placeholders_with_files
from strawberry.http import parse_query_params, parse_request_data
from strawberry.schema.exceptions import InvalidOperationTypeError
from strawberry.types.graphql import OperationType
from strawberry.utils.graphiql import get_graphiql_html

if TYPE_CHECKING:
    from typing_extensions import Literal

    from strawberry.http import GraphQLRequestData
    from strawberry.schema import BaseSchema


class HTTPHandler:
    def __init__(
        self,
        schema: BaseSchema,
        graphiql: bool,
        allow_queries_via_get: bool,
        get_context,
        get_root_value,
        encode_json,
        process_result,
        request: web.Request,
    ):
        self.schema = schema
        self.graphiql = graphiql
        self.allow_queries_via_get = allow_queries_via_get
        self.get_context = get_context
        self.get_root_value = get_root_value
        self.encode_json = encode_json
        self.process_result = process_result
        self.request = request

    async def handle(self) -> web.StreamResponse:
        if self.request.method == "GET":
            return await self.get(self.request)
        if self.request.method == "POST":
            return await self.post(self.request)
        raise web.HTTPMethodNotAllowed(self.request.method, ["GET", "POST"])

    async def get(self, request: web.Request) -> web.StreamResponse:
        if request.query:
            try:
                query_params = {
                    key: request.query.getone(key) for key in set(request.query.keys())
                }
                query_data = parse_query_params(query_params)
                request_data = parse_request_data(query_data)
            except json.JSONDecodeError:
                raise web.HTTPBadRequest(reason="Unable to parse request body as JSON")

            return await self.execute_request(
                request=request, request_data=request_data, method="GET"
            )

        elif self.should_render_graphiql(request):
            return self.render_graphiql()
        raise web.HTTPNotFound()

    async def post(self, request: web.Request) -> web.StreamResponse:
        request_data = await self.get_request_data(request)

        return await self.execute_request(
            request=request, request_data=request_data, method="POST"
        )

    async def execute_request(
        self,
        request: web.Request,
        request_data: GraphQLRequestData,
        method: Union[Literal["GET"], Literal["POST"]],
    ) -> web.StreamResponse:
        response = web.Response()

        context = await self.get_context(request, response)
        root_value = await self.get_root_value(request)

        allowed_operation_types = OperationType.from_http(method)

        if not self.allow_queries_via_get and method == "GET":
            allowed_operation_types = allowed_operation_types - {OperationType.QUERY}

        try:
            result = await self.schema.execute(
                query=request_data.query,
                root_value=root_value,
                variable_values=request_data.variables,
                context_value=context,
                operation_name=request_data.operation_name,
                allowed_operation_types=allowed_operation_types,
            )
        except InvalidOperationTypeError as e:
            raise web.HTTPBadRequest(
                reason=e.as_http_error_reason(method=method)
            ) from e
        except MissingQueryError:
            raise web.HTTPBadRequest(reason="No GraphQL query found in the request")

        response_data = await self.process_result(request, result)

        response.text = self.encode_json(response_data)
        response.content_type = "application/json"

        return response

    async def get_request_data(self, request: web.Request) -> GraphQLRequestData:
        data = await self.parse_body(request)
        return parse_request_data(data)

    async def parse_body(self, request: web.Request) -> dict:
        if request.content_type.startswith("multipart/form-data"):
            return await self.parse_multipart_body(request)
        try:
            return await request.json()
        except json.JSONDecodeError as e:
            raise web.HTTPBadRequest(
                reason="Unable to parse request body as JSON"
            ) from e

    async def parse_multipart_body(self, request: web.Request) -> dict:
        reader = await request.multipart()
        operations: Dict[str, Any] = {}
        files_map: Dict[str, Any] = {}
        files: Dict[str, Any] = {}
        try:
            async for field in reader:
                if field.name == "operations":
                    operations = (await field.json()) or {}
                elif field.name == "map":
                    files_map = (await field.json()) or {}
                elif field.filename:
                    assert field.name

                    files[field.name] = BytesIO(await field.read(decode=False))
        except ValueError:
            raise web.HTTPBadRequest(reason="Unable to parse the multipart body")
        try:
            return replace_placeholders_with_files(operations, files_map, files)
        except KeyError:
            raise web.HTTPBadRequest(reason="File(s) missing in form data")

    def render_graphiql(self) -> web.StreamResponse:
        html_string = get_graphiql_html()

        return web.Response(text=html_string, content_type="text/html")

    def should_render_graphiql(self, request: web.Request) -> bool:
        if not self.graphiql:
            return False

        return any(
            supported_header in request.headers.get("Accept", "")
            for supported_header in ("text/html", "*/*")
        )
