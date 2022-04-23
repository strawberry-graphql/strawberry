from __future__ import annotations

from typing import Dict, Optional

from typing_extensions import Literal

from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
from strawberry.aiohttp.views import GraphQLView as BaseGraphQLView

from ..schema import Query, schema
from . import JSON, HttpClient, Response


class GraphQLView(BaseGraphQLView):
    async def get_root_value(self, request: web.Request):
        return Query()


class AioHttpClient(HttpClient):
    def __init__(self, graphiql: bool = True):
        self.app = web.Application()
        self.app.router.add_route(
            "*", "/graphql", GraphQLView(schema=schema, graphiql=graphiql)
        )

    async def _request(
        self, method: Literal["get", "post"], url: str, **kwargs
    ) -> Response:
        async with TestClient(TestServer(self.app)) as client:
            response = await getattr(client, method)(url, **kwargs)

            return Response(
                status_code=response.status,
                data=(await response.text()).encode(),
            )

    async def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> Response:
        return await self._request("get", url, headers=headers)

    async def post(
        self, url: str, json: JSON, headers: Optional[Dict[str, str]] = None
    ) -> Response:
        return await self._request("post", url, json=json, headers=headers)
