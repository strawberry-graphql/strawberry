from __future__ import annotations

from collections.abc import AsyncIterable

from django.core.exceptions import BadRequest, SuspiciousOperation
from django.http import Http404, HttpRequest, HttpResponse, StreamingHttpResponse

from strawberry.django.views import AsyncGraphQLView as BaseAsyncGraphQLView
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult
from tests.http.context import get_context
from tests.views.schema import Query, schema

from .base import Response, ResultOverrideFunction
from .django import DjangoHttpClient


class AsyncGraphQLView(BaseAsyncGraphQLView[dict[str, object], object]):
    result_override: ResultOverrideFunction = None

    async def get_root_value(self, request: HttpRequest) -> Query:
        await super().get_root_value(request)  # for coverage
        return Query()

    async def get_context(
        self, request: HttpRequest, response: HttpResponse
    ) -> dict[str, object]:
        context = {"request": request, "response": response}

        return get_context(context)

    async def process_result(
        self, request: HttpRequest, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        if self.result_override:
            return self.result_override(result)

        return await super().process_result(request, result)


class AsyncDjangoHttpClient(DjangoHttpClient):
    async def _do_request(self, request: HttpRequest) -> Response:
        view = AsyncGraphQLView.as_view(
            schema=schema,
            graphiql=self.graphiql,
            graphql_ide=self.graphql_ide,
            allow_queries_via_get=self.allow_queries_via_get,
            result_override=self.result_override,
            multipart_uploads_enabled=self.multipart_uploads_enabled,
        )

        try:
            response = await view(request)
        except Http404:
            return Response(status_code=404, data=b"Not found", headers={})
        except (BadRequest, SuspiciousOperation) as e:
            return Response(
                status_code=400,
                data=e.args[0].encode(),
                headers={},
            )

        data = (
            response.streaming_content
            if isinstance(response, StreamingHttpResponse)
            and isinstance(response.streaming_content, AsyncIterable)
            else response.content
        )

        return Response(
            status_code=response.status_code,
            data=data,
            headers=dict(response.headers),
        )
