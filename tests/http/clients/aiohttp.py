from __future__ import annotations

from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
from strawberry.aiohttp.views import GraphQLView as BaseGraphQLView

from ..schema import Query, schema
from . import JSON, HttpClient, Response


class GraphQLView(BaseGraphQLView):
    async def get_root_value(self, request: web.Request):
        return Query()


class AioHttpClient(HttpClient):
    def __init__(self):
        self.app = web.Application()
        self.app.router.add_route("*", "/graphql", GraphQLView(schema=schema))

    async def post(self, url: str, json: JSON) -> Response:
        async with TestClient(TestServer(self.app)) as client:
            response = await client.post(url, json=json)

            return Response(
                status_code=response.status,
                data=(await response.text()).encode(),
            )
