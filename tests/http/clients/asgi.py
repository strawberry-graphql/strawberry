from __future__ import annotations

from typing import Union

from starlette.requests import Request
from starlette.testclient import TestClient
from starlette.websockets import WebSocket

from strawberry.asgi import GraphQL as BaseGraphQLView

from ..schema import Query, schema
from . import JSON, HttpClient, Response


class GraphQLView(BaseGraphQLView):
    async def get_root_value(self, request: Union[WebSocket, Request]) -> Query:
        return Query()


class AsgiHttpClient(HttpClient):
    def __init__(self):
        self.app = GraphQLView(
            schema,
        )
        self.client = TestClient(self.app)

    async def post(self, url: str, json: JSON) -> Response:
        response = self.client.post(url, json=json)

        return Response(status_code=response.status_code, data=response.content)
