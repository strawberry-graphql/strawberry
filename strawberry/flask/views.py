import json

from flask import Response, abort, render_template_string, request
from flask.views import View
from strawberry.exceptions import MissingQueryError
from strawberry.file_uploads.utils import replace_placeholders_with_files
from strawberry.http import GraphQLHTTPResponse, parse_request_data, process_result
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

    def get_context(self, response: Response):
        return {"request": request, "response": response}

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
            data = request.json  # type: ignore

        try:
            request_data = parse_request_data(data)
        except MissingQueryError:
            return Response("No valid query was provided for the request", 400)

        response = Response(status=200, content_type="application/json")
        context = self.get_context(response)

        result = self.schema.execute_sync(
            request_data.query,
            variable_values=request_data.variables,
            context_value=context,
            operation_name=request_data.operation_name,
            root_value=self.get_root_value(),
        )

        response_data = self.process_result(result)
        response.set_data(json.dumps(response_data))

        return response
