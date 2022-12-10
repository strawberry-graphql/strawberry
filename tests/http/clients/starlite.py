from __future__ import annotations

import json
from io import BytesIO
from typing import Dict, Optional
from typing_extensions import Literal

from starlite import Request, Starlite
from starlite.testing import TestClient
from strawberry.http import GraphQLHTTPResponse
from strawberry.starlite import make_graphql_controller
from strawberry.types import ExecutionResult

from ..context import get_context
from ..schema import Query, schema
from . import JSON, HttpClient, Response, ResultOverrideFunction


def custom_context_dependency() -> str:
    return "Hi!"


async def starlite_get_context(request: Request = None):
    return get_context({"request": request})


async def get_root_value(request: Request = None):
    return Query()


class StarliteHttpClient(HttpClient):
    def __init__(
        self,
        graphiql: bool = True,
        allow_queries_via_get: bool = True,
        result_override: ResultOverrideFunction = None,
    ):
        BaseGraphQLController = make_graphql_controller(
            schema=schema,
            path="/graphql",
            graphiql=graphiql,
            context_getter=starlite_get_context,
            root_value_getter=get_root_value,
            allow_queries_via_get=allow_queries_via_get,
        )

        class GraphQLController(BaseGraphQLController):
            async def process_result(
                self, result: ExecutionResult
            ) -> GraphQLHTTPResponse:
                if result_override:
                    return result_override(result)

                return await super().process_result(result)

        self.app = Starlite(route_handlers=[GraphQLController])

        self.client = TestClient(self.app)

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

        if body:
            if method == "get":
                kwargs["params"] = body
            else:
                if files:
                    kwargs["data"] = body
                else:
                    kwargs["content"] = json.dumps(body)

        if files:
            kwargs["files"] = files

        response = getattr(self.client, method)(
            "/graphql",
            headers=self._get_headers(method=method, headers=headers, files=files),
            **kwargs,
        )

        return Response(status_code=response.status_code, data=response.content)

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
