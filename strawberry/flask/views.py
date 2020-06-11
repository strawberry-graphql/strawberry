import json
from typing import Any, Optional

from flask import Response, abort, render_template_string, request
from flask.views import View
from graphql.error import format_error as format_graphql_error

from ..schema import BaseSchema
from .graphiql import render_graphiql_page


class GraphQLView(View):
    methods = ["GET", "POST"]

    def __init__(
        self,
        schema: BaseSchema,
        graphiql: bool = True,
        root_value: Optional[Any] = None,
    ):
        self.graphiql = graphiql
        self.schema = schema
        self.root_value = root_value

    def render_template(self, request, template=None):
        return render_template_string(template)

    def dispatch_request(self):
        if "text/html" in request.environ.get("HTTP_ACCEPT", ""):
            if not self.graphiql:
                abort(404)

            template = render_graphiql_page()
            return self.render_template(request, template=template)

        data = request.json

        try:
            query = data["query"]
            variables = data.get("variables")
            operation_name = data.get("operationName")

        except KeyError:
            return Response("No valid query was provided for the request", 400)

        context = {"request": request}

        result = self.schema.execute_sync(
            query,
            variable_values=variables,
            context_value=context,
            operation_name=operation_name,
            root_value=self.root_value,
        )

        response_data = {"data": result.data}

        if result.errors:
            response_data["errors"] = [
                format_graphql_error(err) for err in result.errors
            ]

        return Response(
            json.dumps(response_data),
            status=400 if result.errors else 200,
            content_type="application/json",
        )
