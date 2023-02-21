from __future__ import annotations

import json
from io import BytesIO
from typing import Dict, Optional, Union
from typing_extensions import Literal

from starlette.requests import Request
from starlette.responses import Response as StarletteResponse
from starlette.testclient import TestClient
from starlette.websockets import WebSocket

from strawberry.asgi import GraphQL as BaseGraphQLView
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult
from tests.views.schema import Query, schema

from ..context import get_context
from . import JSON, HttpClient, Response, ResultOverrideFunction


class GraphQLView(BaseGraphQLView):
    result_override: ResultOverrideFunction = None

    async def get_root_value(self, request: Union[WebSocket, Request]) -> Query:
        return Query()

    async def get_context(
        self,
        request: Union[Request, WebSocket],
        response: Optional[StarletteResponse] = None,
    ) -> object:
        context = await super().get_context(request, response)

        return get_context(context)

    async def process_result(
        self, request: Request, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        if self.result_override:
            return self.result_override(result)

        return await super().process_result(request, result)


class AsgiHttpClient(HttpClient):
    def __init__(
        self,
        graphiql: bool = True,
        allow_queries_via_get: bool = True,
        result_override: ResultOverrideFunction = None,
    ):
        view = GraphQLView(
            schema,
            graphiql=graphiql,
            allow_queries_via_get=allow_queries_via_get,
        )
        view.result_override = result_override

        self.client = TestClient(view)

    async def _graphql_request(
        self,
        method: Literal["get", "post"],
        query: Optional[str] = None,
        variables: Optional[Dict[str, object]] = None,
        files: Optional[Dict[str, BytesIO]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Response:
        body = self._build_body(
            query=query, variables=variables, files=files, method=method
        )

        if method == "get":
            kwargs["params"] = body
        elif body:
            if files:
                kwargs["data"] = body
            else:
                kwargs["content"] = json.dumps(body)

        if files is not None:
            kwargs["files"] = files

        response = getattr(self.client, method)(
            "/graphql",
            headers=self._get_headers(method=method, headers=headers, files=files),
            **kwargs,
        )

        return Response(
            status_code=response.status_code,
            data=response.content,
        )

    async def request(
        self,
        url: str,
        method: Literal["get", "post", "patch", "put", "delete"],
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        response = getattr(self.client, method)(url, headers=headers)

        return Response(
            status_code=response.status_code,
            data=response.content,
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
        response = self.client.post(url, headers=headers, content=data, json=json)

        return Response(
            status_code=response.status_code,
            data=response.content,
        )
