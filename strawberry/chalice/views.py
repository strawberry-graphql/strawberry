import functools
from http import HTTPStatus
from typing import Dict

from chalice.app import Request, Response

from strawberry.schema import BaseSchema
from strawberry.http import GraphQLHTTPResponse, process_result
from strawberry.types import ExecutionResult
from strawberry.chalice.graphiql import render_graphiql_page


class GraphQLView:
    def __init__(self, schema: BaseSchema, render_graphiql=True):
        self._schema: BaseSchema = schema
        self.graphiql: bool = render_graphiql

    @staticmethod
    @functools.lru_cache
    def render_graphiql() -> str:
        """
        Returns a string containing the html for the graphiql webpage. It also caches the result using lru cache
        This saves loading from disk each time it is invoked.
        Returns:

        """
        # We use the same method as strawberry flask as subscriptions are not currently enabled
        result = render_graphiql_page()
        return result

    @staticmethod
    def has_html_been_asked_for(headers: Dict) -> bool:
        """
        Do the headers indicate that the invoker has requested html?
        Args:
            headers: A dictionary containing the headers in the request

        Returns:
            Whether html has been requested True for yes, False for no
        """
        try:
            accept_headers = headers.get("accept")
        except KeyError:
            return False

        if "text/html" in accept_headers:
            return True

        if "*/*" in accept_headers:
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

    def execute_request(self, request: Request) -> Response:
        """
        Parse the request process it with strawberry and return a response
        Args:
            request: The chalice request

        Returns:
            A chalice response
        """
        if self.graphiql:
            if self.has_html_been_asked_for(headers=request.headers) and self.method_is_get(request.method):
                graphiql_page = self.render_graphiql()
                return Response(body=graphiql_page, headers={"content-type": "text/html"}, status_code=200)

        request_data = request.json_body

        try:
            query = request_data["query"]
            variables = request_data.get("variables")
            operation_name = request_data.get("operationName")

        except KeyError:
            return Response(body="Provide a valid query", status_code=HTTPStatus.BAD_REQUEST)

        result: ExecutionResult = self._schema.execute_sync(
            query,
            variable_values=variables,
            context_value=request,
            operation_name=operation_name,
            root_value=None,
        )

        http_result: GraphQLHTTPResponse = process_result(result)

        return Response(body=http_result)
