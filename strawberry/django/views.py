from __future__ import annotations

import json
import warnings
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Optional,
    Union,
)
from typing_extensions import TypeGuard

from asgiref.sync import markcoroutinefunction
from django.core.serializers.json import DjangoJSONEncoder
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseNotAllowed,
    JsonResponse,
    StreamingHttpResponse,
)
from django.http.response import HttpResponseBase
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.utils.decorators import classonlymethod
from django.views.generic import View
from lia import AsyncDjangoHTTPRequestAdapter, DjangoHTTPRequestAdapter, HTTPException

from strawberry.http.async_base_view import AsyncBaseHTTPView
from strawberry.http.sync_base_view import SyncBaseHTTPView
from strawberry.http.typevars import (
    Context,
    RootValue,
)

from .context import StrawberryDjangoContext

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from django.template.response import TemplateResponse

    from strawberry.http import GraphQLHTTPResponse
    from strawberry.http.ides import GraphQL_IDE
    from strawberry.schema import BaseSchema


# TODO: remove this and unify temporal responses
class TemporalHttpResponse(JsonResponse):
    status_code: Optional[int] = None  # pyright: ignore

    def __init__(self) -> None:
        super().__init__({})

    def __repr__(self) -> str:
        """Adopted from Django to handle `status_code=None`."""
        if self.status_code is not None:
            return super().__repr__()

        return "<{cls} status_code={status_code}{content_type}>".format(  # noqa: UP032
            cls=self.__class__.__name__,
            status_code=self.status_code,
            content_type=self._content_type_for_repr,  # pyright: ignore
        )


class BaseView:
    graphql_ide_html: str

    def __init__(
        self,
        schema: BaseSchema,
        graphiql: Optional[str] = None,
        graphql_ide: Optional[GraphQL_IDE] = "graphiql",
        allow_queries_via_get: bool = True,
        multipart_uploads_enabled: bool = False,
        **kwargs: Any,
    ) -> None:
        self.schema = schema
        self.allow_queries_via_get = allow_queries_via_get
        self.multipart_uploads_enabled = multipart_uploads_enabled

        if graphiql is not None:
            warnings.warn(
                "The `graphiql` argument is deprecated in favor of `graphql_ide`",
                DeprecationWarning,
                stacklevel=2,
            )
            self.graphql_ide = "graphiql" if graphiql else None
        else:
            self.graphql_ide = graphql_ide

        super().__init__(**kwargs)

    def create_response(
        self,
        response_data: Union[GraphQLHTTPResponse, list[GraphQLHTTPResponse]],
        sub_response: HttpResponse,
    ) -> HttpResponseBase:
        data = self.encode_json(response_data)

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

    async def create_streaming_response(
        self,
        request: HttpRequest,
        stream: Callable[[], AsyncIterator[Any]],
        sub_response: TemporalHttpResponse,
        headers: dict[str, str],
    ) -> HttpResponseBase:
        return StreamingHttpResponse(
            streaming_content=stream(),
            status=sub_response.status_code,
            headers={
                **sub_response.headers,
                **headers,
            },
        )

    def encode_json(self, data: object) -> str:
        return json.dumps(data, cls=DjangoJSONEncoder)


class GraphQLView(
    BaseView,
    SyncBaseHTTPView[
        HttpRequest, HttpResponseBase, TemporalHttpResponse, Context, RootValue
    ],
    View,
):
    graphiql: Optional[bool] = None
    graphql_ide: Optional[GraphQL_IDE] = "graphiql"
    allow_queries_via_get = True
    schema: BaseSchema = None  # type: ignore
    request_adapter_class = DjangoHTTPRequestAdapter

    def get_root_value(self, request: HttpRequest) -> Optional[RootValue]:
        return None

    def get_context(self, request: HttpRequest, response: HttpResponse) -> Context:
        return StrawberryDjangoContext(request=request, response=response)  # type: ignore

    def get_sub_response(self, request: HttpRequest) -> TemporalHttpResponse:
        return TemporalHttpResponse()

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> Union[HttpResponseNotAllowed, TemplateResponse, HttpResponseBase]:
        try:
            return self.run(request=request)
        except HTTPException as e:
            return HttpResponse(
                content=e.reason,
                status=e.status_code,
            )

    def render_graphql_ide(self, request: HttpRequest) -> HttpResponse:
        try:
            content = render_to_string("graphql/graphiql.html", request=request)
        except TemplateDoesNotExist:
            content = self.graphql_ide_html

        return HttpResponse(content)


class AsyncGraphQLView(
    BaseView,
    AsyncBaseHTTPView[
        HttpRequest,
        HttpResponseBase,
        TemporalHttpResponse,
        HttpRequest,
        TemporalHttpResponse,
        Context,
        RootValue,
    ],
    View,
):
    graphiql: Optional[bool] = None
    graphql_ide: Optional[GraphQL_IDE] = "graphiql"
    allow_queries_via_get = True
    schema: BaseSchema = None  # type: ignore
    request_adapter_class = AsyncDjangoHTTPRequestAdapter

    @classonlymethod  # pyright: ignore[reportIncompatibleMethodOverride]
    def as_view(cls, **initkwargs: Any) -> Callable[..., HttpResponse]:  # noqa: N805
        # This code tells django that this view is async, see docs here:
        # https://docs.djangoproject.com/en/3.1/topics/async/#async-views

        view = super().as_view(**initkwargs)
        markcoroutinefunction(view)

        return view

    async def get_root_value(self, request: HttpRequest) -> Optional[RootValue]:
        return None

    async def get_context(
        self, request: HttpRequest, response: HttpResponse
    ) -> Context:
        return StrawberryDjangoContext(request=request, response=response)  # type: ignore

    async def get_sub_response(self, request: HttpRequest) -> TemporalHttpResponse:
        return TemporalHttpResponse()

    async def dispatch(  # pyright: ignore
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> Union[HttpResponseNotAllowed, TemplateResponse, HttpResponseBase]:
        try:
            return await self.run(request=request)
        except HTTPException as e:
            return HttpResponse(
                content=e.reason,
                status=e.status_code,
            )

    async def render_graphql_ide(self, request: HttpRequest) -> HttpResponse:
        try:
            content = render_to_string("graphql/graphiql.html", request=request)
        except TemplateDoesNotExist:
            content = self.graphql_ide_html

        return HttpResponse(content=content)

    def is_websocket_request(self, request: HttpRequest) -> TypeGuard[HttpRequest]:
        return False

    async def pick_websocket_subprotocol(self, request: HttpRequest) -> Optional[str]:
        raise NotImplementedError

    async def create_websocket_response(
        self, request: HttpRequest, subprotocol: Optional[str]
    ) -> TemporalHttpResponse:
        raise NotImplementedError


__all__ = ["AsyncGraphQLView", "GraphQLView"]
