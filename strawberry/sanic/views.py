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
from strawberry.sanic.context import StrawberrySanicContext
from strawberry.sanic.graphiql import render_graphiql_page, should_render_graphiql
from strawberry.sanic.utils import convert_request_to_files_dict
from strawberry.schema import BaseSchema
from strawberry.types import ExecutionResult


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
        if request.args:
            # Sanic uses urllib to parse
            # This returns a list of values for each variable name
            # Enforcing only one value
            data = {
                variable_name: value[0] for variable_name, value in request.args.items()
            }

            try:
                request_data = parse_request_data(data)
            except MissingQueryError:
                raise ServerError(
                    "No GraphQL query found in the request", status_code=400
                )

            return await self.execute_request(
                request=request, request_data=request_data
            )

        elif should_render_graphiql(self.graphiql, request):
            template = render_graphiql_page()
            return self.render_template(template=template)

        raise SanicException(status_code=404)

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

        return await self.execute_request(request=request, request_data=request_data)

    async def execute_request(
        self, request: Request, request_data: GraphQLRequestData
    ) -> HTTPResponse:
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
            data = self.parse_request(request)
        except json.JSONDecodeError:
            raise ServerError("Unable to parse request body as JSON", status_code=400)

        try:
            request_data = parse_request_data(data)
        except MissingQueryError:
            raise ServerError("No GraphQL query found in the request", status_code=400)

        return request_data

    def parse_request(self, request: Request) -> dict:
        content_type = request.content_type or ""

        if "application/json" in content_type:
            return request.json
        elif content_type.startswith("multipart/form-data"):
            files = convert_request_to_files_dict(request)
            operations = json.loads(request.form.get("operations", "{}"))
            files_map = json.loads(request.form.get("map", "{}"))
            try:
                return replace_placeholders_with_files(operations, files_map, files)
            except KeyError:
                raise SanicException(
                    status_code=400, message="File(s) missing in form data"
                )

        raise ServerError("Unsupported Media Type", status_code=415)
