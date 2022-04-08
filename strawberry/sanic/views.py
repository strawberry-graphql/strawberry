import json
from typing import Any, Dict, Optional, Type

from sanic.exceptions import SanicException, ServerError
from sanic.request import Request
from sanic.response import HTTPResponse, html
from sanic.views import HTTPMethodView
from strawberry.exceptions import MissingQueryError
from strawberry.file_uploads.utils import replace_placeholders_with_files
from strawberry.http import (
    GraphQLHTTPResponse,
    GraphQLRequestData,
    parse_request_data,
    process_result,
)
from strawberry.types import ExecutionResult

from ..schema import BaseSchema
from .context import StrawberrySanicContext
from .graphiql import render_graphiql_page
from .utils import convert_request_to_files_dict


class GraphQLView(HTTPMethodView):
    """
    Class based view to handle GraphQL HTTP Requests

    Args:
        schema: strawberry.Schema
        graphiql: bool, default is True
        json_encoder: json.JSONEncoder, default is JSONEncoder
        json_dumps_params: dict, default is None

    Returns:
        None

    Example:
        app.add_route(
            GraphQLView.as_view(schema=schema, graphiql=True),
            "/graphql"
        )
    """

    def __init__(
        self,
        schema: BaseSchema,
        graphiql: bool = True,
        json_encoder: Type[json.JSONEncoder] = json.JSONEncoder,
        json_dumps_params: Optional[Dict[str, Any]] = None,
    ):
        self.graphiql = graphiql
        self.schema = schema
        self.json_encoder = json_encoder
        self.json_dumps_params = json_dumps_params

    def get_root_value(self):
        return None

    async def get_context(self, request: Request) -> Any:
        return StrawberrySanicContext(request)

    def render_template(self, template=None):
        return html(template)

    def process_result(self, result: ExecutionResult) -> GraphQLHTTPResponse:
        return process_result(result)

    async def get(self, request: Request) -> HTTPResponse:
        if not self.graphiql:
            raise SanicException(status_code=404)

        template = render_graphiql_page()
        return self.render_template(template=template)

    async def get_response(self, response_data: GraphQLHTTPResponse) -> HTTPResponse:
        data = json.dumps(
            response_data, cls=self.json_encoder, **(self.json_dumps_params or {})
        )

        return HTTPResponse(
            data,
            status=200,
            content_type="application/json",
        )

    async def post(self, request: Request) -> HTTPResponse:
        request_data = self.get_request_data(request)
        context = await self.get_context(request)
        root_value = self.get_root_value()

        result = await self.schema.execute(
            query=request_data.query,
            variable_values=request_data.variables,
            context_value=context,
            root_value=root_value,
            operation_name=request_data.operation_name,
        )

        response_data = self.process_result(result)

        return await self.get_response(response_data)

    def get_request_data(self, request: Request) -> GraphQLRequestData:
        try:
            data = self.parse_body(request)
        except json.JSONDecodeError:
            raise ServerError("Unable to parse request body as JSON", status_code=400)

        try:
            request_data = parse_request_data(data)
        except MissingQueryError:
            raise ServerError("No GraphQL query found in the request", status_code=400)

        return request_data

    def parse_body(self, request: Request) -> dict:
        if request.content_type.startswith("multipart/form-data"):
            files = convert_request_to_files_dict(request)
            operations = json.loads(request.form.get("operations", "{}"))
            files_map = json.loads(request.form.get("map", "{}"))
            try:
                return replace_placeholders_with_files(operations, files_map, files)
            except KeyError:
                raise SanicException(
                    status_code=400, message="File(s) missing in form data"
                )
        return request.json
