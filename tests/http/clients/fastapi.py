from __future__ import annotations

import json
from io import BytesIO
from typing import Dict, Optional, Union

from typing_extensions import Literal

from fastapi import BackgroundTasks, Depends, FastAPI, Request, WebSocket
from fastapi.testclient import TestClient
from strawberry.fastapi import GraphQLRouter as BaseGraphQLRouter

from ..schema import Query, schema
from . import JSON, HttpClient, Response


def custom_context_dependency() -> str:
    return "Hi!"


async def get_context(
    background_tasks: BackgroundTasks,
    request: Request = None,
    ws: WebSocket = None,
    custom_value=Depends(custom_context_dependency),
):
    return {
        "custom_value": custom_value,
        "request": request or ws,
        "background_tasks": background_tasks,
    }


async def get_root_value(request: Request = None, ws: WebSocket = None):
    return Query()


class GraphQLRouter(BaseGraphQLRouter):
    ...


class FastAPIHttpClient(HttpClient):
    def __init__(self, graphiql: bool = True):
        self.app = FastAPI()

        graphql_app = GraphQLRouter(
            schema,
            graphiql=graphiql,
            context_getter=get_context,
            root_value_getter=get_root_value,
        )
        self.app.include_router(graphql_app, prefix="/graphql")

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
        body = self._build_body(query, variables, files)

        data: Union[Dict[str, object], str, None] = None

        if body:
            data = body if files else json.dumps(body)

        response = getattr(self.client, method)(
            "/graphql", data=data, headers=headers, files=files, **kwargs
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
        response = self.client.post(url, headers=headers, data=data, json=json)

        return Response(
            status_code=response.status_code,
            data=response.content,
        )
