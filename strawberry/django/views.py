import json
import os

from django.http import Http404, HttpResponseNotAllowed, JsonResponse
from django.http.response import HttpResponseBadRequest
from django.template import RequestContext, Template
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

import strawberry
from graphql import graphql_sync
from graphql.error import format_error as format_graphql_error
from graphql.type.schema import GraphQLSchema


class GraphQLView(View):
    schema = None
    graphiql = True

    def __init__(self, schema=None, graphiql=True):
        if not schema:
            raise ValueError("You must pass in a schema to GraphQLView")

        if not isinstance(schema, GraphQLSchema):
            raise ValueError("You must pass in a valid schema to GraphQLView")

        self.schema = schema
        self.graphiql = graphiql

    def get_root_value(self):
        return None

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        if request.method.lower() not in ("get", "post"):
            return HttpResponseNotAllowed(
                ["GET", "POST"], "GraphQL only supports GET and POST requests."
            )

        if "text/html" in request.META.get("HTTP_ACCEPT", ""):
            if not self.graphiql:
                raise Http404("GraphiQL has been disabled")

            return self._render_graphiql(request)

        data = json.loads(request.body)

        try:
            query = data["query"]
            variables = data.get("variables")
            operation_name = data.get("operationName")
        except KeyError:
            return HttpResponseBadRequest("No GraphQL query found in the request")

        context = {"request": request}

        result = graphql_sync(
            self.schema,
            query,
            root_value=self.get_root_value(),
            variable_values=variables,
            context_value=context,
            operation_name=operation_name,
        )

        response_data = {"data": result.data}

        if result.errors:
            response_data["errors"] = [
                format_graphql_error(err) for err in result.errors
            ]

        return JsonResponse(response_data)

    def _render_graphiql(self, request, context=None):
        try:
            template = Template(render_to_string("graphql/graphiql.html"))
        except TemplateDoesNotExist:
            template = Template(
                open(
                    os.path.join(
                        os.path.dirname(os.path.abspath(strawberry.__file__)),
                        "static/graphiql.html",
                    ),
                    "r",
                ).read()
            )

        context = context or {}
        context.update({"SUBSCRIPTION_ENABLED": "false"})

        response = TemplateResponse(request=request, template=None, context=context)
        response.content = template.render(RequestContext(request, context))

        return response
