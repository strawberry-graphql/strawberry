import json
from typing import Mapping

from flask import Response, render_template_string, request
from flask.views import View
from strawberry.exceptions import MissingQueryError
from strawberry.file_uploads.utils import replace_placeholders_with_files
from strawberry.flask.graphiql import render_graphiql_page, should_render_graphiql
from strawberry.http import (
    GraphQLHTTPResponse,
    parse_query_params,
    parse_request_data,
    process_result,
)
from strawberry.schema.base import BaseSchema
from strawberry.schema.exceptions import InvalidOperationTypeError
from strawberry.types import ExecutionResult
from strawberry.types.graphql import OperationType


class GraphQLView(View):
    methods = ["GET", "POST"]

    def __init__(
        self,
        schema: BaseSchema,
        graphiql: bool = True,
        allow_queries_via_get: bool = True,
    ):
        self.schema = schema
        self.graphiql = graphiql
        self.allow_queries_via_get = allow_queries_via_get

    def get_root_value(self) -> object:
        return None

    def get_context(self, response: Response) -> Mapping[str, object]:
        return {"request": request, "response": response}

    def render_template(self, template: str) -> str:
        return render_template_string(template)

    def process_result(self, result: ExecutionResult) -> GraphQLHTTPResponse:
        return process_result(result)

    def dispatch_request(self) -> Response:
        method = request.method
        content_type = request.content_type or ""

        if "application/json" in content_type:
            data: dict = request.json  # type:ignore[assignment]
        elif content_type.startswith("multipart/form-data"):
            operations = json.loads(request.form.get("operations", "{}"))
            files_map = json.loads(request.form.get("map", "{}"))

            data = replace_placeholders_with_files(operations, files_map, request.files)
        elif method == "GET" and request.args:
            data = parse_query_params(request.args.to_dict())
        elif method == "GET" and should_render_graphiql(self.graphiql, request):
            template = render_graphiql_page()

            return self.render_template(template=template)
        else:
            return Response("Unsupported Media Type", 415)

        try:
            request_data = parse_request_data(data)
        except MissingQueryError:
            return Response("No valid query was provided for the request", 400)

        response = Response(status=200, content_type="application/json")
        context = self.get_context(response)

        allowed_operation_types = OperationType.from_http(method)

        if not self.allow_queries_via_get and method == "GET":
            allowed_operation_types = allowed_operation_types - {OperationType.QUERY}

        try:
            result = self.schema.execute_sync(
                request_data.query,
                variable_values=request_data.variables,
                context_value=context,
                operation_name=request_data.operation_name,
                root_value=self.get_root_value(),
                allowed_operation_types=allowed_operation_types,
            )
        except InvalidOperationTypeError as e:
            return Response(e.as_http_error_reason(method), 400)

        response_data = self.process_result(result)
        response.set_data(json.dumps(response_data))

        return response


class AsyncGraphQLView(GraphQLView):
    async def dispatch_request(self):
        method = request.method
        content_type = request.content_type or ""

        if "application/json" in content_type:
            data: dict = request.json  # type:ignore[assignment]
        elif content_type.startswith("multipart/form-data"):
            operations = json.loads(request.form.get("operations", "{}"))
            files_map = json.loads(request.form.get("map", "{}"))

            data = replace_placeholders_with_files(operations, files_map, request.files)
        elif method == "GET" and request.args:
            data = parse_query_params(request.args.to_dict())
        elif method == "GET" and should_render_graphiql(self.graphiql, request):
            template = render_graphiql_page()

            return self.render_template(template=template)
        else:
            return Response("Unsupported Media Type", 415)

        try:
            request_data = parse_request_data(data)
        except MissingQueryError:
            return Response("No valid query was provided for the request", 400)

        response = Response(status=200, content_type="application/json")
        context = self.get_context(response)

        allowed_operation_types = OperationType.from_http(method)

        if not self.allow_queries_via_get and method == "GET":
            allowed_operation_types = allowed_operation_types - {OperationType.QUERY}

        try:
            result = await self.schema.execute(
                request_data.query,
                variable_values=request_data.variables,
                context_value=context,
                operation_name=request_data.operation_name,
                root_value=self.get_root_value(),
                allowed_operation_types=allowed_operation_types,
            )
        except InvalidOperationTypeError as e:
            return Response(e.as_http_error_reason(method), 400)

        response_data = self.process_result(result)
        response.set_data(json.dumps(response_data))

        return response
