from __future__ import annotations

import json
from io import BytesIO
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
            data = body if files else json.dumps(body)

        response = getattr(self.client, method)(
            "/graphql", data=data, headers=headers, files=files, **kwargs
        )

        return Response(
            status_code=response.status_code,
            data=response.content,
        )

    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        response = self.client.get("/graphql", headers=headers)

        return Response(
            status_code=response.status_code,
            data=response.content,
        )

    async def post(
        self,
        url: str,
        data: Optional[bytes] = None,
        json: Optional[JSON] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        response = self.client.post("/graphql", headers=headers, data=data, json=json)

        return Response(
            status_code=response.status_code,
            data=response.content,
        )
