import asyncio
import json
import os
from typing import Any, Dict, Optional, Type

from django.core.exceptions import BadRequest, SuspiciousOperation
from django.core.serializers.json import DjangoJSONEncoder
from django.http import Http404, HttpRequest, HttpResponseNotAllowed, JsonResponse
from django.http.response import HttpResponse
from django.template import RequestContext, Template
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.utils.decorators import classonlymethod, method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

import strawberry
from strawberry.exceptions import MissingQueryError
from strawberry.file_uploads.utils import replace_placeholders_with_files
from strawberry.http import (
    GraphQLHTTPResponse,
    GraphQLRequestData,
    parse_query_params,
    parse_request_data,
    process_result,
)
from strawberry.schema.exceptions import InvalidOperationTypeError
from strawberry.types import ExecutionResult
from strawberry.types.graphql import OperationType

from ..schema import BaseSchema
from .context import StrawberryDjangoContext


class TemporalHttpResponse(JsonResponse):
    status_code = None

    def __init__(self) -> None:
        super().__init__({})


class BaseView(View):
    subscriptions_enabled = False
    graphiql = True
    allow_queries_via_get = True
    schema: Optional[BaseSchema] = None
    json_encoder: Type[json.JSONEncoder] = DjangoJSONEncoder
    json_dumps_params: Optional[Dict[str, Any]] = None

    def __init__(
        self,
        schema: BaseSchema,
        graphiql=True,
        allow_queries_via_get=True,
        subscriptions_enabled=False,
        **kwargs: Any,
    ):
        self.schema = schema
        self.graphiql = graphiql
        self.allow_queries_via_get = allow_queries_via_get
        self.subscriptions_enabled = subscriptions_enabled
        super().__init__(**kwargs)

    def parse_body(self, request: HttpRequest) -> Dict[str, Any]:
        content_type = request.content_type or ""

        if "application/json" in content_type:
            return json.loads(request.body)
        elif content_type.startswith("multipart/form-data"):
            data = json.loads(request.POST.get("operations", "{}"))
            files_map = json.loads(request.POST.get("map", "{}"))

            data = replace_placeholders_with_files(data, files_map, request.FILES)

            return data
        elif request.method.lower() == "get" and request.META.get("QUERY_STRING"):
            return parse_query_params(request.GET.copy())

        return json.loads(request.body)

    def is_request_allowed(self, request: HttpRequest) -> bool:
        return request.method.lower() in ("get", "post")

    def should_render_graphiql(self, request: HttpRequest) -> bool:
        if request.method.lower() != "get":
            return False

        if request.META.get("QUERY_STRING"):
            return False

        return any(
            supported_header in request.META.get("HTTP_ACCEPT", "")
            for supported_header in ("text/html", "*/*")
        )

    def get_request_data(self, request: HttpRequest) -> GraphQLRequestData:
        try:
            data = self.parse_body(request)
        except json.decoder.JSONDecodeError:
            raise SuspiciousOperation("Unable to parse request body as JSON")

        try:
            request_data = parse_request_data(data)
        except MissingQueryError:
            raise SuspiciousOperation("No GraphQL query found in the request")

        return request_data

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
        context.update({"SUBSCRIPTION_ENABLED": json.dumps(self.subscriptions_enabled)})

        response = TemplateResponse(request=request, template=None, context=context)
        response.content = template.render(RequestContext(request, context))

        return response

    def _create_response(
        self, response_data: GraphQLHTTPResponse, sub_response: HttpResponse
    ) -> JsonResponse:
        response = JsonResponse(
            response_data,
            encoder=self.json_encoder,
            json_dumps_params=self.json_dumps_params,
        )

        for name, value in sub_response.items():
            response[name] = value

        if sub_response.status_code is not None:
            response.status_code = sub_response.status_code

        for name, value in sub_response.cookies.items():
            response.cookies[name] = value

        return response


class GraphQLView(BaseView):
    def get_root_value(self, request: HttpRequest) -> Any:
        return None

    def get_context(self, request: HttpRequest, response: HttpResponse) -> Any:
        return StrawberryDjangoContext(request=request, response=response)

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

        request_data = self.get_request_data(request)

        sub_response = TemporalHttpResponse()
        context = self.get_context(request, response=sub_response)
        root_value = self.get_root_value(request)

        method = request.method
        allowed_operation_types = OperationType.from_http(method)

        if not self.allow_queries_via_get and method == "GET":
            allowed_operation_types = allowed_operation_types - {OperationType.QUERY}

        assert self.schema

        try:
            result = self.schema.execute_sync(
                request_data.query,
                root_value=root_value,
                variable_values=request_data.variables,
                context_value=context,
                operation_name=request_data.operation_name,
                allowed_operation_types=allowed_operation_types,
            )
        except InvalidOperationTypeError as e:
            raise BadRequest(e.as_http_error_reason(method)) from e

        response_data = self.process_result(request=request, result=result)

        return self._create_response(
            response_data=response_data, sub_response=sub_response
        )


class AsyncGraphQLView(BaseView):
    @classonlymethod
    def as_view(cls, **initkwargs):
        # This code tells django that this view is async, see docs here:
        # https://docs.djangoproject.com/en/3.1/topics/async/#async-views

        view = super().as_view(**initkwargs)
        view._is_coroutine = asyncio.coroutines._is_coroutine  # type: ignore[attr-defined] # noqa: E501
        return view

    @method_decorator(csrf_exempt)
    async def dispatch(self, request, *args, **kwargs):
        if not self.is_request_allowed(request):
            return HttpResponseNotAllowed(
                ["GET", "POST"], "GraphQL only supports GET and POST requests."
            )

        if self.should_render_graphiql(request):
            return self._render_graphiql(request)

        request_data = self.get_request_data(request)

        sub_response = TemporalHttpResponse()
        context = await self.get_context(request, response=sub_response)
        root_value = await self.get_root_value(request)

        method = request.method

        allowed_operation_types = OperationType.from_http(method)

        if not self.allow_queries_via_get and method == "GET":
            allowed_operation_types = allowed_operation_types - {OperationType.QUERY}

        assert self.schema

        try:
            result = await self.schema.execute(
                request_data.query,
                root_value=root_value,
                variable_values=request_data.variables,
                context_value=context,
                operation_name=request_data.operation_name,
                allowed_operation_types=allowed_operation_types,
            )
        except InvalidOperationTypeError as e:
            raise BadRequest(e.as_http_error_reason(method)) from e

        response_data = await self.process_result(request=request, result=result)

        return self._create_response(
            response_data=response_data, sub_response=sub_response
        )

    async def get_root_value(self, request: HttpRequest) -> Any:
        return None

    async def get_context(self, request: HttpRequest, response: HttpResponse) -> Any:
        return StrawberryDjangoContext(request=request, response=response)

    async def process_result(
        self, request: HttpRequest, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        return process_result(result)
