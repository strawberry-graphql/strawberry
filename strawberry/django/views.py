from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, Any, Callable, Optional, Union

from django.core.exceptions import BadRequest, SuspiciousOperation
from django.http import HttpRequest, HttpResponseNotAllowed, JsonResponse
from django.http.response import HttpResponse
from django.template import RequestContext, Template
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.utils.decorators import classonlymethod, method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from strawberry.exceptions import MissingQueryError
from strawberry.http import (
    process_result,
)
from strawberry.http.base_view import BaseHTTPView, Context, HTTPException, RootValue
from strawberry.schema.exceptions import InvalidOperationTypeError
from strawberry.types.graphql import OperationType
from strawberry.utils.graphiql import get_graphiql_html

from .context import StrawberryDjangoContext

if TYPE_CHECKING:
    from django.http import HttpRequest

    from strawberry.http import GraphQLHTTPResponse
    from strawberry.types import ExecutionResult

    from ..schema import BaseSchema


# TODO: remove this and unify temporal responses
class TemporalHttpResponse(JsonResponse):
    status_code: Optional[int] = None  # type: ignore

    def __init__(self) -> None:
        super().__init__({})

    def __repr__(self) -> str:
        """Adopted from Django to handle `status_code=None`."""
        if self.status_code is not None:
            return super().__repr__()

        return "<{cls} status_code={status_code}{content_type}>".format(
            cls=self.__class__.__name__,
            status_code=self.status_code,
            content_type=self._content_type_for_repr,  # type: ignore
        )


class BaseView(
    BaseHTTPView[HttpRequest, HttpResponse, Context, RootValue], View  # TODO fix type?
):
    subscriptions_enabled = False
    graphiql = True
    allow_queries_via_get = True  # type: ignore
    schema: BaseSchema = None  # type: ignore

    def __init__(
        self,
        schema: BaseSchema,
        graphiql: bool = True,
        allow_queries_via_get: bool = True,
        subscriptions_enabled: bool = False,
        **kwargs: Any,
    ):
        self.schema = schema
        self.graphiql = graphiql
        self.allow_queries_via_get = allow_queries_via_get
        self.subscriptions_enabled = subscriptions_enabled

        super().__init__(**kwargs)

    def render_graphiql(self, request: HttpRequest) -> TemplateResponse:
        context = None  # TODO?

        try:
            template = Template(render_to_string("graphql/graphiql.html"))
        except TemplateDoesNotExist:
            template = Template(get_graphiql_html(replace_variables=False))

        context = context or {}
        context.update({"SUBSCRIPTION_ENABLED": json.dumps(self.subscriptions_enabled)})

        response = TemplateResponse(request=request, template=None, context=context)
        response.content = template.render(RequestContext(request, context))

        return response

    def get_sub_response(self, request: HttpRequest) -> TemporalHttpResponse:
        return TemporalHttpResponse()

    def _create_response(
        self, response_data: GraphQLHTTPResponse, sub_response: HttpResponse
    ) -> HttpResponse:
        data = self.encode_json(response_data)

        response = HttpResponse(
            data,
            content_type="application/json",
        )

        for name, value in sub_response.items():
            response[name] = value

        if sub_response.status_code is not None:
            response.status_code = sub_response.status_code

        for name, value in sub_response.cookies.items():
            response.cookies[name] = value

        return response


class GraphQLView(BaseView[Context, RootValue]):
    def get_context(self, request: HttpRequest, response: HttpResponse) -> Any:
        return StrawberryDjangoContext(request=request, response=response)

    @method_decorator(csrf_exempt)
    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> Union[HttpResponseNotAllowed, TemplateResponse, HttpResponse]:
        try:
            return self.run(
                request=request,
            )
        except HTTPException as e:
            return HttpResponse(
                content=e.reason,
                status=e.status_code,
            )


class AsyncGraphQLView(BaseView):
    @classonlymethod
    def as_view(cls, **initkwargs) -> Callable[..., HttpResponse]:
        # This code tells django that this view is async, see docs here:
        # https://docs.djangoproject.com/en/3.1/topics/async/#async-views

        view = super().as_view(**initkwargs)
        view._is_coroutine = asyncio.coroutines._is_coroutine  # type: ignore[attr-defined] # noqa: E501
        return view

    @method_decorator(csrf_exempt)
    async def dispatch(
        self, request, *args, **kwargs
    ) -> Union[HttpResponseNotAllowed, TemplateResponse, HttpResponse]:
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
        except MissingQueryError:
            raise SuspiciousOperation("No GraphQL query found in the request")

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
