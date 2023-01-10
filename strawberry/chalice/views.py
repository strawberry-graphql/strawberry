import json
import warnings
from typing import Dict, Mapping, Optional

from chalice.app import BadRequestError, Request, Response
from strawberry.exceptions import MissingQueryError
from strawberry.http import (
    GraphQLHTTPResponse,
    parse_query_params,
    parse_request_data,
    process_result,
)
from strawberry.http.temporal_response import TemporalResponse
from strawberry.schema import BaseSchema
from strawberry.schema.exceptions import InvalidOperationTypeError
from strawberry.types import ExecutionResult
from strawberry.types.graphql import OperationType
from strawberry.utils.graphiql import get_graphiql_html


class GraphQLView:
    def __init__(
        self,
        schema: BaseSchema,
        graphiql: bool = True,
        allow_queries_via_get: bool = True,
        **kwargs
    ):
        if "render_graphiql" in kwargs:
            self.graphiql = kwargs.pop("render_graphiql")
            warnings.warn(
                "The `render_graphiql` argument is deprecated. "
                "Use `graphiql` instead.",
                DeprecationWarning,
            )
        else:
            self.graphiql = graphiql

        self.allow_queries_via_get = allow_queries_via_get
        self._schema = schema

    def get_root_value(self, request: Request) -> Optional[object]:
        return None

    @staticmethod
    def render_graphiql() -> str:
        """
        Returns a string containing the html for the graphiql webpage. It also caches
        the result using lru cache.
        This saves loading from disk each time it is invoked.

        Returns:
            The GraphiQL html page as a string
        """
        return get_graphiql_html(subscription_enabled=False)

    @staticmethod
    def should_render_graphiql(graphiql: bool, request: Request) -> bool:
        """
        Do the headers indicate that the invoker has requested html?
        Args:
            headers: A dictionary containing the headers in the request

        Returns:
            Whether html has been requested True for yes, False for no
        """
        if not graphiql:
            return False

        return any(
            supported_header in request.headers.get("accept", "")
            for supported_header in {"text/html", "*/*"}
        )

    @staticmethod
    def error_response(
        message: str,
        error_code: str,
        http_status_code: int,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        """
        A wrapper for error responses
        Returns:
        An errors response
        """
        body = {"Code": error_code, "Message": message}

        return Response(body=body, status_code=http_status_code, headers=headers)

    def get_context(
        self, request: Request, response: TemporalResponse
    ) -> Mapping[str, object]:
        return {"request": request, "response": response}

    def process_result(
        self, request: Request, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        return process_result(result)

    def execute_request(self, request: Request) -> Response:
        """
        Parse the request process it with strawberry and return a response
        Args:
            request: The chalice request this contains the headers and body

        Returns:
            A chalice response
        """

        method = request.method

        if method not in {"POST", "GET"}:
            return self.error_response(
                error_code="MethodNotAllowedError",
                message="Unsupported method, must be of request type POST or GET",
                http_status_code=405,
            )
        content_type = request.headers.get("content-type", "")

        if "application/json" in content_type:
            try:
                data = request.json_body
                if not (isinstance(data, dict)):
                    return self.error_response(
                        error_code="BadRequestError",
                        message=(
                            "Provide a valid graphql query "
                            "in the body of your request"
                        ),
                        http_status_code=400,
                    )
            except BadRequestError:
                return self.error_response(
                    error_code="BadRequestError",
                    message="Unable to parse request body as JSON",
                    http_status_code=400,
                )
        elif method == "GET" and request.query_params:
            try:
                data = parse_query_params(request.query_params)  # type: ignore
            except json.JSONDecodeError:
                return self.error_response(
                    error_code="BadRequestError",
                    message="Unable to parse request body as JSON",
                    http_status_code=400,
                )

        elif method == "GET" and self.should_render_graphiql(self.graphiql, request):
            return Response(
                body=self.render_graphiql(),
                headers={"content-type": "text/html"},
                status_code=200,
            )

        else:
            return self.error_response(
                error_code="NotFoundError",
                message="Not found",
                http_status_code=404,
            )

        request_data = parse_request_data(data)

        allowed_operation_types = OperationType.from_http(method)

        if not self.allow_queries_via_get and method == "GET":
            allowed_operation_types = allowed_operation_types - {OperationType.QUERY}

        context = self.get_context(request, response=TemporalResponse())

        try:
            result: ExecutionResult = self._schema.execute_sync(
                request_data.query,
                variable_values=request_data.variables,
                context_value=context,
                operation_name=request_data.operation_name,
                root_value=self.get_root_value(request),
                allowed_operation_types=allowed_operation_types,
            )

        except InvalidOperationTypeError as e:
            return self.error_response(
                error_code="BadRequestError",
                message=e.as_http_error_reason(method),
                http_status_code=400,
            )
        except MissingQueryError:
            return self.error_response(
                error_code="BadRequestError",
                message="No GraphQL query found in the request",
                http_status_code=400,
            )

        http_result: GraphQLHTTPResponse = self.process_result(request, result)

        status_code = 200

        if "response" in context:
            # TODO: we might want to use typed dict for context
            status_code = context["response"].status_code  # type: ignore[attr-defined]

        return Response(body=self.encode_json(http_result), status_code=status_code)

    def encode_json(self, response_data: GraphQLHTTPResponse) -> str:
        return json.dumps(response_data)
