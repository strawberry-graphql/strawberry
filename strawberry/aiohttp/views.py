import json
from io import BytesIO
from pathlib import Path

from aiohttp import web
from strawberry.file_uploads.data import replace_placeholders_with_files
from strawberry.http import GraphQLHTTPResponse, process_result
from strawberry.schema import BaseSchema
from strawberry.types import ExecutionContext, ExecutionResult


class GraphQLView:
    def __init__(self, schema: BaseSchema, graphiql: bool = True):
        self.schema = schema
        self.graphiql = graphiql

    async def __call__(self, request: web.Request) -> web.StreamResponse:
        if request.method == "GET":
            return await self.get(request)
        if request.method == "POST":
            return await self.post(request)
        raise web.HTTPMethodNotAllowed(request.method, ["GET", "POST"])

    async def get_root_value(self, request: web.Request) -> object:
        return None

    async def get_context(self, request: web.Request) -> object:
        return {"request": request}

    async def process_result(
        self, request: web.Request, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        return process_result(result)

    async def get(self, request: web.Request) -> web.Response:
        if self.should_render_graphiql(request):
            return self.render_graphiql()
        return web.HTTPNotFound()

    async def post(self, request: web.Request) -> web.Response:
        operation_context = await self.get_execution_context(request)
        context = await self.get_context(request)
        root_value = await self.get_root_value(request)

        result = await self.schema.execute(
            query=operation_context.query,
            root_value=root_value,
            variable_values=operation_context.variables,
            context_value=context,
            operation_name=operation_context.operation_name,
        )

        response_data = await self.process_result(request, result)
        return web.json_response(response_data)

    async def get_execution_context(self, request: web.Request) -> ExecutionContext:
        try:
            data = await self.parse_body(request)
        except json.JSONDecodeError:
            raise web.HTTPBadRequest(reason="Unable to parse request body as JSON")

        try:
            query = data["query"]
        except KeyError:
            raise web.HTTPBadRequest(reason="No GraphQL query found in the request")

        variables = data.get("variables")
        operation_name = data.get("operationName")

        return ExecutionContext(
            query=query,
            variables=variables,
            operation_name=operation_name,
        )

    async def parse_body(self, request: web.Request) -> dict:
        if request.content_type.startswith("multipart/form-data"):
            reader = await request.multipart()
            operations = {}
            files_map = {}
            files = {}
            async for field in reader:
                if field.name == "operations":
                    operations = await field.json()
                elif field.name == "map":
                    files_map = await field.json()
                elif field.filename:
                    files[field.name] = BytesIO(await field.read(decode=False))
            return replace_placeholders_with_files(operations, files_map, files)
        return await request.json()

    def render_graphiql(self) -> web.Response:
        html_string = self.graphiql_html_file_path.read_text()
        html_string = html_string.replace("{{ SUBSCRIPTION_ENABLED }}", "false")
        return web.Response(text=html_string, content_type="text/html")

    def should_render_graphiql(self, request: web.Request) -> bool:
        if not self.graphiql:
            return False
        return "text/html" in request.headers.get("Accept", "")

    @property
    def graphiql_html_file_path(self) -> Path:
        return Path(__file__).parent.parent / "static" / "graphiql.html"
