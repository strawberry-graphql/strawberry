from __future__ import annotations

from io import BytesIO
from json import dumps
from random import randint
from typing import Dict, Optional

from typing_extensions import Literal

from sanic import Sanic
from sanic.request import Request as SanicRequest
from strawberry.http.temporal_response import TemporalResponse
from strawberry.sanic.views import GraphQLView as BaseGraphQLView

from ..context import get_context
from ..schema import Query, schema
from . import JSON, HttpClient, Response


class GraphQLView(BaseGraphQLView):
    def get_root_value(self):
        return Query()

    async def get_context(
        self, request: SanicRequest, response: TemporalResponse
    ) -> object:
        context = {"request": request, "response": response}

        return get_context(context)


class SanicHttpClient(HttpClient):
    def __init__(self, graphiql: bool = True, allow_queries_via_get: bool = True):
        self.app = Sanic(
            f"test_{int(randint(0, 1000))}",
            log_config={
                "version": 1,
                "loggers": {},
                "handlers": {},
            },
        )
        self.app.add_route(
            GraphQLView.as_view(
                schema=schema,
                graphiql=graphiql,
                allow_queries_via_get=allow_queries_via_get,
            ),
            "/graphql",
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
        body = self._build_body(
            query=query, variables=variables, files=files, method=method
        )

        if body:
            if method == "get":
                kwargs["params"] = body
            else:
                kwargs["data"] = body if files else dumps(body)

        request, response = await self.app.asgi_client.request(
            method,
            "/graphql",
            headers=self._get_headers(method=method, headers=headers, files=files),
            files=files,
            **kwargs,
        )

        return Response(status_code=response.status_code, data=response.content)

    async def request(
        self,
        url: str,
        method: Literal["get", "post", "patch", "put", "delete"],
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        request, response = await self.app.asgi_client.request(
            method,
            url,
            headers=headers,
        )

        return Response(status_code=response.status_code, data=response.content)

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
        body = data or dumps(json)
        request, response = await self.app.asgi_client.request(
            "post", url, data=body, headers=headers
        )

        return Response(status_code=response.status_code, data=response.content)
