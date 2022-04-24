from __future__ import annotations

from io import BytesIO
from json import dumps
from random import randint
from typing import Dict, Optional, Union

from typing_extensions import Literal

from sanic import Sanic
from strawberry.sanic.views import GraphQLView as BaseGraphQLView

from ..schema import Query, schema
from . import JSON, HttpClient, Response


class GraphQLView(BaseGraphQLView):
    def get_root_value(self):
        return Query()


class SanicHttpClient(HttpClient):
    def __init__(self, graphiql: bool = True):
        self.app = Sanic(
            f"test_{int(randint(0, 1000))}",
            log_config={
                "version": 1,
                "loggers": {},
                "handlers": {},
            },
        )
        self.app.add_route(
            GraphQLView.as_view(schema=schema, graphiql=graphiql), "/graphql"
        )

    async def _request(
        self,
        method: Literal["get", "post"],
        query: Optional[str] = None,
        variables: Optional[Dict[str, object]] = None,
        files: Optional[Dict[str, BytesIO]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Response:
        body = self._build_body(query, variables, files)

        data: Union[Dict[str, object], str, None] = None

        if body:
            data = body if files else dumps(body)

        request, response = await self.app.asgi_client.request(
            method, "/graphql", data=data, headers=headers, files=files, **kwargs
        )

        return Response(status_code=response.status_code, data=response.content)

    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        request, response = await self.app.asgi_client.request(
            "get",
            "/graphql",
            headers=headers,
        )

        return Response(status_code=response.status_code, data=response.content)

    async def post(
        self,
        url: str,
        data: Optional[bytes] = None,
        json: Optional[JSON] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        body = data or dumps(json)
        request, response = await self.app.asgi_client.request(
            "post", "/graphql", data=body, headers=headers
        )

        return Response(status_code=response.status_code, data=response.content)
