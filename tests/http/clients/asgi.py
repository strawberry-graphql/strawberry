from __future__ import annotations

from typing import Dict, Optional, Union

from starlette.requests import Request
from starlette.testclient import TestClient
from starlette.websockets import WebSocket
from typing_extensions import Literal

from strawberry.asgi import GraphQL as BaseGraphQLView

from ..schema import Query, schema
from . import JSON, HttpClient, Response


class GraphQLView(BaseGraphQLView):
    async def get_root_value(self, request: Union[WebSocket, Request]) -> Query:
        return Query()


class AsgiHttpClient(HttpClient):
    def __init__(self, graphiql: bool = True):
        self.app = GraphQLView(schema, graphiql=graphiql)
        self.client = TestClient(self.app)

    async def _request(
        self, method: Literal["get", "post"], url: str, **kwargs
    ) -> Response:
        response = getattr(self.client, method)(url, **kwargs)

        return Response(
            status_code=response.status_code,
            data=response.content,
        )

    async def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> Response:
        return await self._request("get", url, headers=headers)

    async def post(
        self, url: str, json: JSON, headers: Optional[Dict[str, str]] = None
    ) -> Response:
        return await self._request("post", url, json=json, headers=headers)
