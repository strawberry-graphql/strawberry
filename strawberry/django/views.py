from __future__ import annotations

import asyncio
import json
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Mapping,
    Optional,
    Union,
    cast,
)

from django.http import HttpRequest, HttpResponseNotAllowed, JsonResponse
from django.http.response import HttpResponse
from django.template import RequestContext, Template
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.utils.decorators import classonlymethod, method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from strawberry.http.async_base_view import AsyncBaseHTTPView, AsyncHTTPRequestAdapter
from strawberry.http.exceptions import HTTPException
from strawberry.http.sync_base_view import SyncBaseHTTPView, SyncHTTPRequestAdapter
from strawberry.http.types import FormData, HTTPMethod, QueryParams
from strawberry.http.typevars import (
    Context,
    RootValue,
)
from strawberry.utils.graphiql import get_graphiql_html

from .context import StrawberryDjangoContext

if TYPE_CHECKING:
    from strawberry.http import GraphQLHTTPResponse

    from ..schema import BaseSchema


# TODO: remove this and unify temporal responses
class TemporalHttpResponse(JsonResponse):
    status_code: Optional[int] = None  # pyright: ignore

    def __init__(self) -> None:
        super().__init__({})

    def __repr__(self) -> str:
        """Adopted from Django to handle `status_code=None`."""
        if self.status_code is not None:
            return super().__repr__()

        return "<{cls} status_code={status_code}{content_type}>".format(
            cls=self.__class__.__name__,
            status_code=self.status_code,
            content_type=self._content_type_for_repr,  # pyright: ignore
        )


class DjangoHTTPRequestAdapter(SyncHTTPRequestAdapter):
    def __init__(self, request: HttpRequest):
        self.request = request

    @property
    def query_params(self) -> QueryParams:
        return self.request.GET.dict()

    @property
    def body(self) -> Union[str, bytes]:
        return self.request.body.decode()

    @property
    def method(self) -> HTTPMethod:
        assert self.request.method is not None

        return cast(HTTPMethod, self.request.method.upper())

    @property
    def headers(self) -> Mapping[str, str]:
        return self.request.headers

    @property
    def post_data(self) -> Mapping[str, Union[str, bytes]]:
        return self.request.POST

    @property
    def files(self) -> Mapping[str, Any]:
        return self.request.FILES

    @property
    def content_type(self) -> Optional[str]:
        return self.request.content_type


class AsyncDjangoHTTPRequestAdapter(AsyncHTTPRequestAdapter):
    def __init__(self, request: HttpRequest):
        self.request = request

    @property
    def query_params(self) -> QueryParams:
        return self.request.GET.dict()

    @property
    def method(self) -> HTTPMethod:
        assert self.request.method is not None

        return cast(HTTPMethod, self.request.method.upper())

    @property
    def headers(self) -> Mapping[str, str]:
        return self.request.headers

    @property
    def content_type(self) -> Optional[str]:
        return self.request.content_type

    async def get_body(self) -> str:
        return self.request.body.decode()

    async def get_form_data(self) -> FormData:
        return FormData(
            files=self.request.FILES,
            form=self.request.POST,
        )


class BaseView:
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

    def render_graphiql(self, request: HttpRequest) -> HttpResponse:
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

    def create_response(
        self, response_data: GraphQLHTTPResponse, sub_response: HttpResponse
    ) -> HttpResponse:
        data = self.encode_json(response_data)  # type: ignore

        response = HttpResponse(
            data,
            content_type="application/json",
        )

        for name, value in sub_response.items():
            response[name] = value

        if sub_response.status_code:
            response.status_code = sub_response.status_code

        for name, value in sub_response.cookies.items():
            response.cookies[name] = value

        return response


class GraphQLView(
    BaseView,
    SyncBaseHTTPView[
        HttpRequest, HttpResponse, TemporalHttpResponse, Context, RootValue
    ],
    View,
):
    subscriptions_enabled = False
    graphiql = True
    allow_queries_via_get = True
    schema: BaseSchema = None  # type: ignore
    request_adapter_class = DjangoHTTPRequestAdapter

    def get_root_value(self, request: HttpRequest) -> Optional[RootValue]:
        return None

    def get_context(self, request: HttpRequest, response: HttpResponse) -> Any:
        return StrawberryDjangoContext(request=request, response=response)

    def get_sub_response(self, request: HttpRequest) -> TemporalHttpResponse:
        return TemporalHttpResponse()

    @method_decorator(csrf_exempt)
    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> Union[HttpResponseNotAllowed, TemplateResponse, HttpResponse]:
        try:
            return self.run(request=request)
        except HTTPException as e:
            return HttpResponse(
                content=e.reason,
                status=e.status_code,
            )


class AsyncGraphQLView(
    BaseView,
    AsyncBaseHTTPView[
        HttpRequest, HttpResponse, TemporalHttpResponse, Context, RootValue
    ],
    View,
):
    subscriptions_enabled = False
    graphiql = True
    allow_queries_via_get = True
    schema: BaseSchema = None  # type: ignore
    request_adapter_class = AsyncDjangoHTTPRequestAdapter

    @classonlymethod
    def as_view(cls, **initkwargs: Any) -> Callable[..., HttpResponse]:
        # This code tells django that this view is async, see docs here:
        # https://docs.djangoproject.com/en/3.1/topics/async/#async-views

        view = super().as_view(**initkwargs)
        view._is_coroutine = asyncio.coroutines._is_coroutine  # type: ignore[attr-defined] # noqa: E501
        return view

    async def get_root_value(self, request: HttpRequest) -> Any:
        return None

    async def get_context(self, request: HttpRequest, response: HttpResponse) -> Any:
        return StrawberryDjangoContext(request=request, response=response)

    async def get_sub_response(self, request: HttpRequest) -> TemporalHttpResponse:
        return TemporalHttpResponse()

    @method_decorator(csrf_exempt)
    async def dispatch(  # pyright: ignore
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> Union[HttpResponseNotAllowed, TemplateResponse, HttpResponse]:
        try:
            return await self.run(request=request)
        except HTTPException as e:
            return HttpResponse(
                content=e.reason,
                status=e.status_code,
            )
