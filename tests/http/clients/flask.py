from __future__ import annotations

import json
from io import BytesIO
from typing import Dict, Optional, Union

from typing_extensions import Literal

from flask import Flask
from strawberry.flask.views import GraphQLView as BaseGraphQLView

from ..schema import Query, schema
from . import JSON, HttpClient, Response


class GraphQLView(BaseGraphQLView):
    def get_root_value(self):
        return Query()


class FlaskHttpClient(HttpClient):
    def __init__(self, graphiql: bool = True):
        self.app = Flask(__name__)
        self.app.debug = True

        self.app.add_url_rule(
            "/graphql",
            view_func=GraphQLView.as_view(
                "graphql_view", schema=schema, graphiql=graphiql
            ),
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

        if body and files:
            body.update({name: (file, name) for name, file in files.items()})

        if body:
            data = body if files else json.dumps(body)

        with self.app.test_client() as client:
            response = getattr(client, method)(
                "/graphql",
                data=data,
                headers=headers,
                **kwargs,
            )

        return Response(
            status_code=response.status_code,
            data=response.data,
        )

    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        with self.app.test_client() as client:
            response = client.get("/graphql", headers=headers)

        return Response(
            status_code=response.status_code,
            data=response.data,
        )

    async def post(
        self,
        url: str,
        json: JSON,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        with self.app.test_client() as client:
            response = client.post("/graphql", headers=headers, json=json)

        return Response(
            status_code=response.status_code,
            data=response.data,
        )
