import json
from io import BytesIO
from pathlib import Path
from typing import Any, Optional, Type

import aiohttp.web
from strawberry.file_uploads.data import replace_placeholders_with_files
from strawberry.http import GraphQLHTTPResponse, process_result
from strawberry.schema import BaseSchema
from strawberry.types import ExecutionContext, ExecutionResult


class GraphQLView(aiohttp.web.View):
    graphiql = True
    schema: Optional[BaseSchema] = None

    async def get_root_value(self) -> Any:
        return None

    async def get_context(self) -> Any:
        return {"request": self.request}

    async def process_result(self, result: ExecutionResult) -> GraphQLHTTPResponse:
        return process_result(result)

    async def get(self) -> aiohttp.web.Response:
        if self.should_render_graphiql:
            return self.render_graphiql()
        return aiohttp.web.HTTPNotFound()

    async def post(self) -> aiohttp.web.Response:
        operation_context = await self.get_execution_context()
        context = await self.get_context()
        root_value = await self.get_root_value()

        result = await self.schema.execute(
            query=operation_context.query,
            root_value=root_value,
            variable_values=operation_context.variables,
            context_value=context,
            operation_name=operation_context.operation_name,
        )

        response_data = await self.process_result(result)
        return aiohttp.web.json_response(response_data)

    async def get_execution_context(self) -> ExecutionContext:
        try:
            data = await self.parse_body()
        except json.JSONDecodeError:
            raise aiohttp.web.HTTPBadRequest(
                reason="Unable to parse request body as JSON"
            )

        try:
            query = data["query"]
            variables = data.get("variables")
            operation_name = data.get("operationName")
        except KeyError:
            raise aiohttp.web.HTTPBadRequest(
                reason="No GraphQL query found in the request"
            )

        return ExecutionContext(
            query=query,
            variables=variables,
            operation_name=operation_name,
        )

    async def parse_body(self) -> dict:
        if self.request.content_type.startswith("multipart/form-data"):
            reader = await self.request.multipart()
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
        return await self.request.json()

    def render_graphiql(self) -> aiohttp.web.Response:
        with open(self.graphiql_html_file_path, "r") as f:
            html_string = f.read()
        html_string = html_string.replace("{{ SUBSCRIPTION_ENABLED }}", "false")
        return aiohttp.web.Response(text=html_string, content_type="text/html")

    @property
    def graphiql_html_file_path(self) -> Path:
        return Path(__file__).parent.parent / "static" / "graphiql.html"

    @property
    def should_render_graphiql(self) -> bool:
        if not self.graphiql:
            return False
        return "text/html" in self.request.headers.get("Accept", "")

    @classmethod
    def as_view(cls, schema: BaseSchema, graphiql=True) -> Type["GraphQLView"]:
        cls.schema = schema
        cls.graphiql = graphiql
        return cls
