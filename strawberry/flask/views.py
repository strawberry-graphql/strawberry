import json

from flask import Response, abort, render_template_string, request
from flask.views import View
from strawberry.file_uploads.data import replace_placeholders_with_files
from strawberry.http import GraphQLHTTPResponse, process_result
from strawberry.types import ExecutionResult

from ..schema import BaseSchema
from .graphiql import render_graphiql_page


class GraphQLView(View):
    methods = ["GET", "POST"]

    def __init__(
        self,
        schema: BaseSchema,
        graphiql: bool = True,
    ):
        self.graphiql = graphiql
        self.schema = schema

    def get_root_value(self):
        return None

    def get_context(self):
        return {"request": request}

    def render_template(self, template=None):
        return render_template_string(template)

    def process_result(self, result: ExecutionResult) -> GraphQLHTTPResponse:
        return process_result(result)

    def dispatch_request(self):
        if "text/html" in request.environ.get("HTTP_ACCEPT", ""):
            if not self.graphiql:
                abort(404)

            template = render_graphiql_page()
            return self.render_template(template=template)

        if request.content_type.startswith("multipart/form-data"):
            operations = json.loads(request.form.get("operations", "{}"))
            files_map = json.loads(request.form.get("map", "{}"))

            data = replace_placeholders_with_files(operations, files_map, request.files)

        else:
            data = request.json

        try:
            query = data["query"]
            variables = data.get("variables")
            operation_name = data.get("operationName")

        except KeyError:
            return Response("No valid query was provided for the request", 400)

        context = self.get_context()

        result = self.schema.execute_sync(
            query,
            variable_values=variables,
            context_value=context,
            operation_name=operation_name,
            root_value=self.get_root_value(),
        )

        response_data = self.process_result(result)

        return Response(
            json.dumps(response_data),
            status=200,
            content_type="application/json",
        )
