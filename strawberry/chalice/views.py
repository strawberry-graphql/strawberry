import functools
from http import HTTPStatus

from chalice.app import CaseInsensitiveMapping, Request, Response
from strawberry.chalice.graphiql import render_graphiql_page
from strawberry.http import GraphQLHTTPResponse, process_result
from strawberry.schema import BaseSchema
from strawberry.types import ExecutionResult


class GraphQLView:
    def __init__(self, schema: BaseSchema, render_graphiql: bool = True):
        self._schema = schema
        self.graphiql = render_graphiql

    @staticmethod
    @functools.lru_cache()
    def render_graphiql() -> str:
        """
        Returns a string containing the html for the graphiql webpage. It also caches the
        result using lru cache. This saves loading from disk each time it is invoked.
        Returns:

        """
        result = render_graphiql_page()
        return result

    @staticmethod
    def has_html_been_asked_for(headers: CaseInsensitiveMapping) -> bool:
        """
        Do the headers indicate that the invoker has requested html?
        Args:
            headers: A dictionary containing the headers in the request

        Returns:
            Whether html has been requested True for yes, False for no
        """
        try:
            accept_headers = headers.get("accept")
        except (KeyError, TypeError):
            return False

        if accept_headers is None:
            return False

        if "text/html" in accept_headers:
            return True

        if "*/*" in accept_headers:
            return True

        return False

    @staticmethod
    def method_is_post(method: str) -> bool:
        """
        If the get method has been called this is True
        Args:
            method: A request verb such as GET, POST, PUT etc.

        Returns:
            True if the method is post
        """
        if method == "POST":
            return True

        return False

    @staticmethod
    def method_is_get(method: str) -> bool:
        """
        If the get method has been called this is True
        Args:
            method: A request verb such as GET, POST, PUT etc.

        Returns:
            True if the method is get
        """
        if method == "GET":
            return True

        return False

    @staticmethod
    def invalid_query_response() -> Response:
        """
        A response for malformed queries
        Returns:
        An errors response
        """
        return Response(
            body={"errors": ["Provide a valid query / body to your call"]},
            status_code=HTTPStatus.OK,
        )

    @staticmethod
    def invalid_rest_verb_response() -> Response:
        """
        A response for calling the graphql endpoint with a non POST request
        Returns:

        """
        return Response(
            body={"errors": ["GraphQL queries must be of request type POST"]},
            status_code=HTTPStatus.OK,
        )

    def execute_request(self, request: Request) -> Response:
        """
        Parse the request process it with strawberry and return a response
        Args:
            request: The chalice request this contains the headers and body

        Returns:
            A chalice response
        """
        if self.graphiql:
            if self.has_html_been_asked_for(
                headers=request.headers
            ) and self.method_is_get(request.method):
                graphiql_page: str = self.render_graphiql()
                return Response(
                    body=graphiql_page,
                    headers={"content-type": "text/html"},
                    status_code=200,
                )

        if not self.method_is_post(request.method):
            return self.invalid_rest_verb_response()

        request_data = request.json_body

        if request_data is None:
            return self.invalid_query_response()
        try:
            query = request_data["query"]
            variables = request_data.get("variables")
            operation_name = request_data.get("operationName")

        except (KeyError, TypeError):
            return self.invalid_query_response()

        result: ExecutionResult = self._schema.execute_sync(
            query,
            variable_values=variables,
            context_value=request,
            operation_name=operation_name,
            root_value=None,
        )

        http_result: GraphQLHTTPResponse = process_result(result)

        return Response(body=http_result)
