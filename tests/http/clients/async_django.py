from __future__ import annotations

from collections.abc import AsyncIterable
from typing import Optional

from django.core.exceptions import BadRequest, SuspiciousOperation
from django.http import Http404, HttpRequest, HttpResponse, StreamingHttpResponse

from strawberry.django.views import AsyncGraphQLView as BaseAsyncGraphQLView
from strawberry.http import GraphQLHTTPResponse
from strawberry.http.ides import GraphQL_IDE
from strawberry.schema.config import StrawberryConfig
from strawberry.types import ExecutionResult
from tests.http.context import get_context
from tests.views.schema import Query, get_schema

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
    def __init__(
        self,
        graphiql: Optional[bool] = None,
        graphql_ide: Optional[GraphQL_IDE] = "graphiql",
        allow_queries_via_get: bool = True,
        result_override: ResultOverrideFunction = None,
        multipart_uploads_enabled: bool = False,
        schema_config: Optional[StrawberryConfig] = None,
    ):
        self.view = AsyncGraphQLView.as_view(
            schema=get_schema(schema_config),
            graphiql=graphiql,
            graphql_ide=graphql_ide,
            allow_queries_via_get=allow_queries_via_get,
            result_override=result_override,
            multipart_uploads_enabled=multipart_uploads_enabled,
        )

    async def _do_request(self, request: HttpRequest) -> Response:
        try:
            response = await self.view(request)
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
