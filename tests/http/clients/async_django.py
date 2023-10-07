from __future__ import annotations

from django.core.exceptions import BadRequest, SuspiciousOperation
from django.http import Http404, HttpRequest, HttpResponse
from django.test.client import RequestFactory

from strawberry.django.views import AsyncGraphQLView as BaseAsyncGraphQLView
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult
from tests.views.schema import Query, schema

from ..context import get_context
from .base import Response, ResultOverrideFunction
from .django import DjangoHttpClient


class AsyncGraphQLView(BaseAsyncGraphQLView):
    result_override: ResultOverrideFunction = None

    async def get_root_value(self, request: HttpRequest) -> Query:
        await super().get_root_value(request)  # for coverage
        return Query()

    async def get_context(self, request: HttpRequest, response: HttpResponse) -> object:
        context = {"request": request, "response": response}

        return get_context(context)

    async def process_result(
        self, request: HttpRequest, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        if self.result_override:
            return self.result_override(result)

        return await super().process_result(request, result)


class AsyncDjangoHttpClient(DjangoHttpClient):
    async def _do_request(self, request: RequestFactory) -> Response:
        view = AsyncGraphQLView.as_view(
            schema=schema,
            graphiql=self.graphiql,
            allow_queries_via_get=self.allow_queries_via_get,
            result_override=self.result_override,
        )

        try:
            response = await view(request)
        except Http404:
            return Response(
                status_code=404, data=b"Not found", headers=response.headers
            )
        except (BadRequest, SuspiciousOperation) as e:
            return Response(
                status_code=400, data=e.args[0].encode(), headers=response.headers
            )
        else:
            return Response(
                status_code=response.status_code,
                data=response.content,
                headers=response.headers,
            )
