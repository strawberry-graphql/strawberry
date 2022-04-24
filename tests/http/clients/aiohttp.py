from __future__ import annotations

import json
from typing import Dict, Optional, Union

from typing_extensions import Literal

from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
from strawberry.aiohttp.views import GraphQLView as BaseGraphQLView

from ..schema import Query, schema
from . import HttpClient, Response


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
        self,
        method: Literal["get", "post"],
        query: Optional[str] = None,
        variables: Optional[Dict[str, object]] = None,
        files: Optional[Dict[str, object]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Response:
        async with TestClient(TestServer(self.app)) as client:
            body = self._build_body(query, variables, files)

            data: Union[Dict[str, object], str, None] = None

            if body and files:
                body.update(files)
                data = body
            elif body:
                data = json.dumps(body)

            response = await getattr(client, method)(
                "/graphql", data=data, headers=headers, **kwargs
            )

            return Response(
                status_code=response.status,
                data=(await response.text()).encode(),
            )
