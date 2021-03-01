import json

from sanic.exceptions import abort
from sanic.response import HTTPResponse, html
from sanic.views import HTTPMethodView
from strawberry.http import GraphQLHTTPResponse, process_result
from strawberry.types import ExecutionResult

from ..schema import BaseSchema
from .graphiql import render_graphiql_page


class GraphQLView(HTTPMethodView):
    """
    Class based view to handle GraphQL HTTP Requests

    Args:
        schema: strawberry.Schema
        graphiql: bool, default is True

    Returns:
        None

    Example:
        app.add_route(
            GraphQLView.as_view(schema=schema, graphiql=True),
            "/graphql"
        )
    """

    methods = ["GET", "POST"]

    def __init__(self, schema: BaseSchema, graphiql: bool = True):
        self.graphiql = graphiql
        self.schema = schema

    def get_root_value(self):
        return None

    def get_context(self, request):
        return {"request": request}

    def render_template(self, template=None):
        return html(template)

    def process_result(self, result: ExecutionResult) -> GraphQLHTTPResponse:
        return process_result(result)

    async def dispatch_request(self, request):
        request_method = request.method.lower()
        if not self.graphiql:
            abort(404)

        show_graphiql = request_method == "get" and self.should_display_graphiql(
            request
        )

        if show_graphiql:
            template = render_graphiql_page()
            return self.render_template(template=template)

        data = request.json

        try:
            query = data["query"]
            variables = data.get("variables")
            operation_name = data.get("operationName")

        except KeyError:
            return HTTPResponse("No valid query was provided for the request", 400)

        context = self.get_context(request)

        result = await self.schema.execute(
            query,
            variable_values=variables,
            context_value=context,
            operation_name=operation_name,
            root_value=self.get_root_value(),
        )

        response_data = self.process_result(result)

        return HTTPResponse(
            json.dumps(response_data), status=200, content_type="application/json"
        )

    def should_display_graphiql(self, request):
        if not self.graphiql or "raw" in request.args:
            return False
        return self.request_wants_html(request)

    @staticmethod
    def request_wants_html(request):
        accept = request.headers.get("accept", {})
        return "text/html" in accept or "*/*" in accept
