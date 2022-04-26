from __future__ import annotations

import urllib.parse
from io import BytesIO
from json import dumps
from typing import Dict, Optional, Union

from typing_extensions import Literal

from chalice.app import Chalice, Request as ChaliceRequest
from chalice.test import Client
from strawberry.chalice.views import GraphQLView as BaseGraphQLView

from ..schema import Query, schema
from . import JSON, HttpClient, Response


class GraphQLView(BaseGraphQLView):
    def get_root_value(self, request: ChaliceRequest) -> Query:
        return Query()


class ChaliceHttpClient(HttpClient):
    def __init__(self, graphiql: bool = True, allow_queries_via_get: bool = True):
        self.app = Chalice(app_name="TheStackBadger")

        view = GraphQLView(
            schema=schema,
            graphiql=graphiql,
            allow_queries_via_get=allow_queries_via_get,
        )

        @self.app.route(
            "/graphql", methods=["GET", "POST"], content_types=["application/json"]
        )
        def handle_graphql():
            return view.execute_request(self.app.current_request)

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

        data: Union[Dict[str, object], str, None] = None

        if body and files:
            body.update({name: (file, name) for name, file in files.items()})

        url = "/graphql"

        if method == "get":
            body_encoded = urllib.parse.urlencode(body or {})
            url = f"{url}?{body_encoded}"
        else:
            if body:
                data = body if files else dumps(body)
            kwargs["body"] = data

        with Client(self.app) as client:
            response = getattr(client.http, method)(
                url,
                headers=self._get_headers(method=method, headers=headers, files=files),
                **kwargs,
            )

        return Response(
            status_code=response.status_code,
            data=response.body,
        )

    async def request(
        self,
        url: str,
        method: Literal["get", "post", "patch", "put", "delete"],
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        with Client(self.app) as client:
            response = getattr(client.http, method)(url, headers=headers)

        return Response(
            status_code=response.status_code,
            data=response.body,
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
        body = data or dumps(json)

        with Client(self.app) as client:
            response = client.http.post(url, headers=headers, body=body)

        return Response(
            status_code=response.status_code,
            data=response.body,
        )
