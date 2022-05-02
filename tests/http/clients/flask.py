from __future__ import annotations

import json
import urllib.parse
from io import BytesIO
from typing import Dict, Optional, Union

from typing_extensions import Literal

from flask import Flask, Response as FlaskResponse
from strawberry.flask.views import GraphQLView as BaseGraphQLView

from ..context import get_context
from ..schema import Query, schema
from . import JSON, HttpClient, Response


class GraphQLView(BaseGraphQLView):
    # this allows to test our code path for checking the request type
    # TODO: we might want to remove our check since it is done by flask
    # already
    methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"]

    def get_root_value(self):
        return Query()

    def get_context(self, response: FlaskResponse) -> Dict[str, object]:
        context = super().get_context(response)

        return get_context(context)


class FlaskHttpClient(HttpClient):
    def __init__(self, graphiql: bool = True, allow_queries_via_get: bool = True):
        self.app = Flask(__name__)
        self.app.debug = True

        self.app.add_url_rule(
            "/graphql",
            view_func=GraphQLView.as_view(
                "graphql_view",
                schema=schema,
                graphiql=graphiql,
                allow_queries_via_get=allow_queries_via_get,
            ),
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

        data: Union[Dict[str, object], str, None] = None

        if body and files:
            body.update({name: (file, name) for name, file in files.items()})

        url = "/graphql"

        if method == "get":
            body_encoded = urllib.parse.urlencode(body or {})
            url = f"{url}?{body_encoded}"
        else:
            if body:
                data = body if files else json.dumps(body)
            kwargs["data"] = data

        with self.app.test_client() as client:
            response = getattr(client, method)(
                url,
                headers=self._get_headers(method=method, headers=headers, files=files),
                **kwargs,
            )

        return Response(
            status_code=response.status_code,
            data=response.data,
        )

    async def request(
        self,
        url: str,
        method: Literal["get", "post", "patch", "put", "delete"],
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        with self.app.test_client() as client:
            response = getattr(client, method)(url, headers=headers)

        return Response(
            status_code=response.status_code,
            data=response.data,
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
        with self.app.test_client() as client:
            response = client.post(url, headers=headers, data=data, json=json)

        return Response(
            status_code=response.status_code,
            data=response.data,
        )
