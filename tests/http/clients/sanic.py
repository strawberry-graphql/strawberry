from __future__ import annotations

from io import BytesIO
from json import dumps
from random import randint
from typing import Any, Optional
from typing_extensions import Literal

from sanic import Sanic
from sanic.request import Request as SanicRequest
from strawberry.http import GraphQLHTTPResponse
from strawberry.http.ides import GraphQL_IDE
from strawberry.http.temporal_response import TemporalResponse
from strawberry.sanic.views import GraphQLView as BaseGraphQLView
from strawberry.types import ExecutionResult
from tests.http.context import get_context
from tests.views.schema import Query, schema

from .base import JSON, HttpClient, Response, ResultOverrideFunction


class GraphQLView(BaseGraphQLView[object, Query]):
    result_override: ResultOverrideFunction = None

    def __init__(self, *args: Any, **kwargs: Any):
        self.result_override = kwargs.pop("result_override")
        super().__init__(*args, **kwargs)

    async def get_root_value(self, request: SanicRequest) -> Query:
        await super().get_root_value(request)  # for coverage
        return Query()

    async def get_context(
        self, request: SanicRequest, response: TemporalResponse
    ) -> object:
        context = await super().get_context(request, response)

        return get_context(context)

    async def process_result(
        self, request: SanicRequest, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        if self.result_override:
            return self.result_override(result)

        return await super().process_result(request, result)


class SanicHttpClient(HttpClient):
    def __init__(
        self,
        graphiql: Optional[bool] = None,
        graphql_ide: Optional[GraphQL_IDE] = "graphiql",
        allow_queries_via_get: bool = True,
        result_override: ResultOverrideFunction = None,
        multipart_uploads_enabled: bool = False,
    ):
        self.app = Sanic(
            f"test_{int(randint(0, 1000))}",  # noqa: S311
        )
        view = GraphQLView.as_view(
            schema=schema,
            graphiql=graphiql,
            graphql_ide=graphql_ide,
            allow_queries_via_get=allow_queries_via_get,
            result_override=result_override,
            multipart_uploads_enabled=multipart_uploads_enabled,
        )
        self.app.add_route(
            view,
            "/graphql",
        )

    async def _graphql_request(
        self,
        method: Literal["get", "post"],
        query: Optional[str] = None,
        variables: Optional[dict[str, object]] = None,
        files: Optional[dict[str, BytesIO]] = None,
        headers: Optional[dict[str, str]] = None,
        **kwargs: Any,
    ) -> Response:
        body = self._build_body(
            query=query, variables=variables, files=files, method=method
        )

        if body:
            if method == "get":
                kwargs["params"] = body
            elif files:
                kwargs["data"] = body
            else:
                kwargs["content"] = dumps(body)

        request, response = await self.app.asgi_client.request(
            method,
            "/graphql",
            headers=self._get_headers(method=method, headers=headers, files=files),
            files=files,
            **kwargs,
        )

        return Response(
            status_code=response.status_code,
            data=response.content,
            headers=response.headers,
        )

    async def request(
        self,
        url: str,
        method: Literal["get", "post", "patch", "put", "delete"],
        headers: Optional[dict[str, str]] = None,
    ) -> Response:
        request, response = await self.app.asgi_client.request(
            method,
            url,
            headers=headers,
        )

        return Response(
            status_code=response.status_code,
            data=response.content,
            headers=response.headers,
        )

    async def get(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
    ) -> Response:
        return await self.request(url, "get", headers=headers)

    async def post(
        self,
        url: str,
        data: Optional[bytes] = None,
        json: Optional[JSON] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> Response:
        body = data or dumps(json)
        request, response = await self.app.asgi_client.request(
            "post", url, content=body, headers=headers
        )

        return Response(
            status_code=response.status_code,
            data=response.content,
            headers=response.headers,
        )
