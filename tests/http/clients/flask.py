from __future__ import annotations

from flask import Flask
from strawberry.flask.views import GraphQLView as BaseGraphQLView

from ..schema import Query, schema
from . import JSON, HttpClient, Response


class GraphQLView(BaseGraphQLView):
    def get_root_value(self):
        return Query()


class FlaskHttpClient(HttpClient):
    def __init__(self):
        self.app = Flask(__name__)
        self.app.debug = True

        self.app.add_url_rule(
            "/graphql",
            view_func=GraphQLView.as_view("graphql_view", schema=schema),
        )

    async def post(self, url: str, json: JSON) -> Response:
        with self.app.test_client() as client:
            response = client.post(url, json=json)

            return Response(
                status_code=response.status_code,
                data=response.data,
            )
