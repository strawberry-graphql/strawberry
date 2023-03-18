from __future__ import annotations

import json
import warnings
from typing import TYPE_CHECKING, Any, Dict, Optional, Type, Union

from sanic.exceptions import NotFound, SanicException, ServerError
from sanic.response import HTTPResponse, html
from sanic.views import HTTPMethodView
from strawberry.exceptions import MissingQueryError
from strawberry.file_uploads.utils import replace_placeholders_with_files
from strawberry.http import (
    parse_query_params,
    parse_request_data,
    process_result,
)
from strawberry.http.temporal_response import TemporalResponse
from strawberry.sanic.graphiql import should_render_graphiql
from strawberry.sanic.utils import convert_request_to_files_dict
from strawberry.schema.exceptions import InvalidOperationTypeError
from strawberry.types.graphql import OperationType
from strawberry.utils.graphiql import get_graphiql_html

if TYPE_CHECKING:
    from typing_extensions import Literal

    from sanic.request import Request
    from strawberry.http import GraphQLHTTPResponse, GraphQLRequestData
    from strawberry.schema import BaseSchema
    from strawberry.types import ExecutionResult

    from .context import StrawberrySanicContext


class GraphQLView(HTTPMethodView):
    """
    Class based view to handle GraphQL HTTP Requests

    Args:
        schema: strawberry.Schema
        graphiql: bool, default is True
        allow_queries_via_get: bool, default is True

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
        allow_queries_via_get: bool = True,
        json_encoder: Optional[Type[json.JSONEncoder]] = None,
        json_dumps_params: Optional[Dict[str, Any]] = None,
    ):
        self.schema = schema
        self.graphiql = graphiql
        self.allow_queries_via_get = allow_queries_via_get
        self.json_encoder = json_encoder
        self.json_dumps_params = json_dumps_params

        if self.json_encoder is not None:
            warnings.warn(
                "json_encoder is deprecated, override encode_json instead",
                DeprecationWarning,
            )

        if self.json_dumps_params is not None:
            warnings.warn(
                "json_dumps_params is deprecated, override encode_json instead",
                DeprecationWarning,
            )

            self.json_encoder = json.JSONEncoder

    def get_root_value(self):
        return None

    async def get_context(
        self, request: Request, response: TemporalResponse
    ) -> StrawberrySanicContext:
        return {"request": request, "response": response}

    def render_template(self, template: str) -> HTTPResponse:
        return html(template)

    async def process_result(
        self, request: Request, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        return process_result(result)

    async def get(self, request: Request) -> HTTPResponse:
        if request.args:
            # Sanic request.args uses urllib.parse.parse_qs
            # returns a dictionary where the keys are the unique variable names
            # and the values are a list of values for each variable name
            # Enforcing using the first value
            query_data = {
                variable_name: value[0] for variable_name, value in request.args.items()
            }
            try:
                data = parse_query_params(query_data)
            except json.JSONDecodeError:
                raise ServerError(
                    "Unable to parse request body as JSON", status_code=400
                )

            request_data = parse_request_data(data)

            return await self.execute_request(
                request=request, request_data=request_data, method="GET"
            )

        elif should_render_graphiql(self.graphiql, request):
            template = get_graphiql_html(False)
            return self.render_template(template=template)

        raise NotFound()

    async def get_response(
        self, response_data: GraphQLHTTPResponse, context: StrawberrySanicContext
    ) -> HTTPResponse:
        status_code = 200

        if "response" in context and context["response"]:
            status_code = context["response"].status_code

        data = self.encode_json(response_data)

        return HTTPResponse(
            data,
            status=status_code,
            content_type="application/json",
        )

    def encode_json(self, response_data: GraphQLHTTPResponse) -> str:
        if self.json_dumps_params:
            assert self.json_encoder

            return json.dumps(
                response_data, cls=self.json_encoder, **self.json_dumps_params
            )

        if self.json_encoder:
            return json.dumps(response_data, cls=self.json_encoder)

        return json.dumps(response_data)

    async def post(self, request: Request) -> HTTPResponse:
        request_data = self.get_request_data(request)

        return await self.execute_request(
            request=request, request_data=request_data, method="POST"
        )

    async def execute_request(
        self,
        request: Request,
        request_data: GraphQLRequestData,
        method: Union[Literal["GET"], Literal["POST"]],
    ) -> HTTPResponse:
        context = await self.get_context(request, TemporalResponse())
        root_value = self.get_root_value()

        allowed_operation_types = OperationType.from_http(method)

        if not self.allow_queries_via_get and method == "GET":
            allowed_operation_types = allowed_operation_types - {OperationType.QUERY}

        try:
            result = await self.schema.execute(
                query=request_data.query,
                variable_values=request_data.variables,
                context_value=context,
                root_value=root_value,
                operation_name=request_data.operation_name,
                allowed_operation_types=allowed_operation_types,
            )
        except InvalidOperationTypeError as e:
            raise ServerError(
                e.as_http_error_reason(method=method), status_code=400
            ) from e
        except MissingQueryError:
            raise ServerError("No GraphQL query found in the request", status_code=400)

        response_data = await self.process_result(request, result)

        return await self.get_response(response_data, context)

    def get_request_data(self, request: Request) -> GraphQLRequestData:
        try:
            data = self.parse_request(request)
        except json.JSONDecodeError:
            raise ServerError("Unable to parse request body as JSON", status_code=400)

        return parse_request_data(data)

    def parse_request(self, request: Request) -> Dict[str, Any]:
        content_type = request.content_type or ""

        if "application/json" in content_type:
            return json.loads(request.body)
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
