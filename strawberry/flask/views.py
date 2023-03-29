from __future__ import annotations

import json
from typing import TYPE_CHECKING, Dict, Optional

from flask import Request, Response, render_template_string, request
from flask.views import View
from strawberry.exceptions import MissingQueryError
from strawberry.file_uploads.utils import replace_placeholders_with_files
from strawberry.flask.graphiql import should_render_graphiql
from strawberry.http import (
    parse_query_params,
    parse_request_data,
    process_result,
)
from strawberry.http.base_view import BaseHTTPView, Context, HTTPException, RootValue
from strawberry.schema.exceptions import InvalidOperationTypeError
from strawberry.types.graphql import OperationType
from strawberry.utils.graphiql import get_graphiql_html

if TYPE_CHECKING:
    from flask.typing import ResponseReturnValue
    from strawberry.http import GraphQLHTTPResponse
    from strawberry.schema.base import BaseSchema
    from strawberry.types import ExecutionResult


class BaseGraphQLView(BaseHTTPView[Request, Response, Context, RootValue], View):
    methods = ["GET", "POST"]
    allow_queries_via_get: bool = True

    def __init__(
        self,
        schema: BaseSchema,
        graphiql: bool = True,
        allow_queries_via_get: bool = True,
    ):
        self.schema = schema
        self.graphiql = graphiql
        self.allow_queries_via_get = allow_queries_via_get

    def render_graphiql(self, request: Request) -> Response:
        template = get_graphiql_html(False)

        return render_template_string(template)

    def get_sub_response(self, request: Request) -> Response:
        return Response(status=200, content_type="application/json")


class GraphQLView(BaseGraphQLView[Context, RootValue]):
    def get_context(self, request: Request, response: Response) -> Context:
        return {"request": request, "response": response}

    def get_root_value(self, request: Request) -> Optional[RootValue]:
        return None

    def dispatch_request(self) -> ResponseReturnValue:
        try:
            return self.run(
                request=request,
            )
        except HTTPException as e:
            return Response(
                response=e.reason,
                status=e.status_code,
            )

    def _create_response(
        self, response_data: GraphQLHTTPResponse, sub_response: Response
    ) -> Response:
        sub_response.set_data(self.encode_json(response_data))

        return sub_response


class AsyncGraphQLView(BaseGraphQLView):
    methods = ["GET", "POST"]

    async def get_root_value(self) -> object:
        return None

    # breaking change!
    async def get_context(
        self, request: Request, response: Response
    ) -> Dict[str, object]:
        return {"request": request, "response": response}

    async def process_result(self, result: ExecutionResult) -> GraphQLHTTPResponse:
        return process_result(result)

    async def dispatch_request(self) -> ResponseReturnValue:  # type: ignore[override]
        method = request.method
        content_type = request.content_type or ""

        if request.method not in {"POST", "GET"}:
            return Response(
                "Unsupported method, must be of request type POST or GET", 405
            )

        if "application/json" in content_type:
            try:
                data = json.loads(request.data)
            except json.JSONDecodeError:
                return Response(
                    status=400, response="Unable to parse request body as JSON"
                )
        elif content_type.startswith("multipart/form-data"):
            try:
                operations = json.loads(request.form.get("operations", "{}"))
                files_map = json.loads(request.form.get("map", "{}"))
            except json.JSONDecodeError:
                return Response(
                    status=400, response="Unable to parse request body as JSON"
                )

            try:
                data = replace_placeholders_with_files(
                    operations, files_map, request.files
                )
            except KeyError:
                return Response(status=400, response="File(s) missing in form data")
        elif method == "GET" and request.args:
            try:
                data = parse_query_params(request.args.to_dict())
            except json.JSONDecodeError:
                return Response(
                    status=400, response="Unable to parse request body as JSON"
                )

        elif method == "GET" and should_render_graphiql(self.graphiql, request):
            template = get_graphiql_html(False)

            return self.render_template(template=template)
        elif method == "GET":
            return Response(status=404)
        else:
            return Response("Unsupported Media Type", 415)

        request_data = parse_request_data(data)

        response = Response(status=200, content_type="application/json")
        context = await self.get_context(response)

        allowed_operation_types = OperationType.from_http(method)

        if not self.allow_queries_via_get and method == "GET":
            allowed_operation_types = allowed_operation_types - {OperationType.QUERY}

        root_value = await self.get_root_value()

        try:
            result = await self.schema.execute(
                request_data.query,
                variable_values=request_data.variables,
                context_value=context,
                operation_name=request_data.operation_name,
                root_value=root_value,
                allowed_operation_types=allowed_operation_types,
            )
        except InvalidOperationTypeError as e:
            return Response(e.as_http_error_reason(method), 400)
        except MissingQueryError:
            return Response("No GraphQL query found in the request", 400)

        response_data = await self.process_result(result)
        response.set_data(self.encode_json(response_data))

        return response
