import json
from io import BytesIO
from pathlib import Path
from typing import Any, Dict

from aiohttp import web
from strawberry.exceptions import MissingQueryError
from strawberry.file_uploads.utils import replace_placeholders_with_files
from strawberry.http import GraphQLRequestData, parse_request_data
from strawberry.schema import BaseSchema


class HTTPHandler:
    def __init__(
        self,
        schema: BaseSchema,
        graphiql: bool,
        get_context,
        get_root_value,
        process_result,
        request: web.Request,
    ):
        self.schema = schema
        self.graphiql = graphiql
        self.get_context = get_context
        self.get_root_value = get_root_value
        self.process_result = process_result
        self.request = request

    async def handle(self) -> web.StreamResponse:
        if self.request.method == "GET":
            return await self.get(self.request)
        if self.request.method == "POST":
            return await self.post(self.request)
        raise web.HTTPMethodNotAllowed(self.request.method, ["GET", "POST"])

    async def get(self, request: web.Request) -> web.StreamResponse:
        if self.should_render_graphiql(request):
            return self.render_graphiql()
        return web.HTTPNotFound()

    async def post(self, request: web.Request) -> web.StreamResponse:
        request_data = await self.get_request_data(request)
        response = web.Response()
        context = await self.get_context(request, response)
        root_value = await self.get_root_value(request)

        result = await self.schema.execute(
            query=request_data.query,
            root_value=root_value,
            variable_values=request_data.variables,
            context_value=context,
            operation_name=request_data.operation_name,
        )

        response_data = await self.process_result(request, result)
        response.text = json.dumps(response_data)
        response.content_type = "application/json"
        return response

    async def get_request_data(self, request: web.Request) -> GraphQLRequestData:
        data = await self.parse_body(request)

        try:
            request_data = parse_request_data(data)
        except MissingQueryError:
            raise web.HTTPBadRequest(reason="No GraphQL query found in the request")

        return request_data

    async def parse_body(self, request: web.Request) -> dict:
        if request.content_type.startswith("multipart/form-data"):
            return await self.parse_multipart_body(request)
        try:
            return await request.json()
        except json.JSONDecodeError:
            raise web.HTTPBadRequest(reason="Unable to parse request body as JSON")

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
        html_string = self.graphiql_html_file_path.read_text()
        html_string = html_string.replace("{{ SUBSCRIPTION_ENABLED }}", "true")
        return web.Response(text=html_string, content_type="text/html")

    def should_render_graphiql(self, request: web.Request) -> bool:
        if not self.graphiql:
            return False
        return "text/html" in request.headers.get("Accept", "")

    @property
    def graphiql_html_file_path(self) -> Path:
        return Path(__file__).parent.parent.parent / "static" / "graphiql.html"
