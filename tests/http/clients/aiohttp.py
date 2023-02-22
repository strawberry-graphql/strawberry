from __future__ import annotations

import json
from io import BytesIO
from typing import Dict, Optional
from typing_extensions import Literal

from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
from strawberry.aiohttp.views import GraphQLView as BaseGraphQLView
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult
from tests.views.schema import Query, schema

from ..context import get_context
from . import JSON, HttpClient, Response, ResultOverrideFunction


class GraphQLView(BaseGraphQLView):
    result_override: ResultOverrideFunction = None

    async def get_context(
        self, request: web.Request, response: web.StreamResponse
    ) -> object:
        context = await super().get_context(request, response)

        return get_context(context)

    async def get_root_value(self, request: web.Request):
        return Query()

    async def process_result(
        self, request: web.Request, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        if self.result_override:
            return self.result_override(result)

        return await super().process_result(request, result)


class AioHttpClient(HttpClient):
    def __init__(
        self,
        graphiql: bool = True,
        allow_queries_via_get: bool = True,
        result_override: ResultOverrideFunction = None,
    ):
        view = GraphQLView(
            schema=schema,
            graphiql=graphiql,
            allow_queries_via_get=allow_queries_via_get,
        )
        view.result_override = result_override

        self.app = web.Application()
        self.app.router.add_route(
            "*",
            "/graphql",
            view,
        )

    async def _graphql_request(
        self,
        method: Literal["get", "post"],
        query: Optional[str] = None,
        variables: Optional[Dict[str, object]] = None,
        files: Optional[Dict[str, BytesIO]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Response:
        async with TestClient(TestServer(self.app)) as client:
            body = self._build_body(
                query=query, variables=variables, files=files, method=method
            )

            if body and files:
                body.update(files)

            if method == "get":
                kwargs["params"] = body
            else:
                kwargs["data"] = body if files else json.dumps(body)

            response = await getattr(client, method)(
                "/graphql",
                headers=self._get_headers(method=method, headers=headers, files=files),
                **kwargs,
            )

            return Response(
                status_code=response.status,
                data=(await response.text()).encode(),
            )

    async def request(
        self,
        url: str,
        method: Literal["get", "post", "patch", "put", "delete"],
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        async with TestClient(TestServer(self.app)) as client:
            response = await getattr(client, method)(url, headers=headers)

            return Response(
                status_code=response.status,
                data=(await response.text()).encode(),
            )

    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        return await self.request(url, "get", headers=headers)

    async def post(
        self,
        url: str,
        data: Optional[bytes] = None,
        json: Optional[JSON] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        async with TestClient(TestServer(self.app)) as client:
            response = await client.post(
                "/graphql", headers=headers, data=data, json=json
            )

            return Response(
                status_code=response.status,
                data=(await response.text()).encode(),
            )
