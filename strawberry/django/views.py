import asyncio
import json
import os
from typing import Any, Dict, Optional

from django.core.exceptions import SuspiciousOperation
from django.http import Http404, HttpRequest, HttpResponseNotAllowed, JsonResponse
from django.template import RequestContext, Template
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.utils.decorators import classonlymethod, method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

import strawberry
from strawberry.file_uploads.data import replace_placeholders_with_files
from strawberry.http import GraphQLHTTPResponse, process_result
from strawberry.types import ExecutionResult
from strawberry.types.execution import ExecutionContext

from ..schema import BaseSchema


class BaseView(View):
    graphiql = True
    schema: Optional[BaseSchema] = None

    def __init__(self, schema: BaseSchema, graphiql=True):
        self.schema = schema
        self.graphiql = graphiql

    def parse_body(self, request) -> Dict[str, Any]:
        if request.content_type == "multipart/form-data":
            data = json.loads(request.POST.get("operations", "{}"))
            files_map = json.loads(request.POST.get("map", "{}"))

            data = replace_placeholders_with_files(data, files_map, request.FILES)

            return data

        return json.loads(request.body)

    def is_request_allowed(self, request: HttpRequest) -> bool:
        return request.method.lower() in ("get", "post")

    def should_render_graphiql(self, request: HttpRequest) -> bool:
        return "text/html" in request.META.get("HTTP_ACCEPT", "")

    def get_execution_context(self, request: HttpRequest) -> ExecutionContext:
        data = self.parse_body(request)

        try:
            query = data["query"]
            variables = data.get("variables")
            operation_name = data.get("operationName")
        except KeyError:
            raise SuspiciousOperation("No GraphQL query found in the request")

        return ExecutionContext(
            query=query, variables=variables, operation_name=operation_name
        )

    def _render_graphiql(self, request: HttpRequest, context=None):
        if not self.graphiql:
            raise Http404()

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


class GraphQLView(BaseView):
    def get_root_value(self, request: HttpRequest) -> Any:
        return None

    def get_context(self, request: HttpRequest) -> Any:
        return {"request": request}

    def process_result(
        self, request: HttpRequest, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        return process_result(result)

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        if not self.is_request_allowed(request):
            return HttpResponseNotAllowed(
                ["GET", "POST"], "GraphQL only supports GET and POST requests."
            )

        if self.should_render_graphiql(request):
            return self._render_graphiql(request)

        operation_context = self.get_execution_context(request)
        context = self.get_context(request)

        result = self.schema.execute_sync(
            operation_context.query,
            root_value=self.get_root_value(request),
            variable_values=operation_context.variables,
            context_value=context,
            operation_name=operation_context.operation_name,
        )

        response_data = self.process_result(request=request, result=result)

        return JsonResponse(response_data)


class AsyncGraphQLView(BaseView):
    @classonlymethod
    def as_view(cls, **initkwargs):
        # This code tells django that this view is async, see docs here:
        # https://docs.djangoproject.com/en/3.1/topics/async/#async-views

        view = super().as_view(**initkwargs)
        view._is_coroutine = asyncio.coroutines._is_coroutine
        return view

    @method_decorator(csrf_exempt)
    async def dispatch(self, request, *args, **kwargs):
        if not self.is_request_allowed(request):
            return HttpResponseNotAllowed(
                ["GET", "POST"], "GraphQL only supports GET and POST requests."
            )

        if self.should_render_graphiql(request):
            return self._render_graphiql(request)

        operation_context = self.get_execution_context(request)
        context = await self.get_context(request)
        root_value = await self.get_root_value(request)

        result = await self.schema.execute(
            operation_context.query,
            root_value=root_value,
            variable_values=operation_context.variables,
            context_value=context,
            operation_name=operation_context.operation_name,
        )

        response_data = await self.process_result(request=request, result=result)

        return JsonResponse(response_data)

    async def get_root_value(self, request: HttpRequest) -> Any:
        return None

    async def get_context(self, request: HttpRequest) -> Any:
        return {"request": request}

    async def process_result(
        self, request: HttpRequest, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        return process_result(result)
