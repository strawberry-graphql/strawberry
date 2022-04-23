from __future__ import annotations

from typing import Dict, Optional

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
        self, method: Literal["get", "post"], url: str, **kwargs
    ) -> Response:
        with self.app.test_client() as client:
            response = getattr(client, method)(url, **kwargs)

            return Response(
                status_code=response.status_code,
                data=response.data,
            )

    async def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> Response:
        return await self._request("get", url, headers=headers)

    async def post(
        self, url: str, json: JSON, headers: Optional[Dict[str, str]] = None
    ) -> Response:
        return await self._request("post", url, json=json, headers=headers)
