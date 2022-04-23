from __future__ import annotations

from random import randint

from sanic import Sanic
from strawberry.sanic.views import GraphQLView as BaseGraphQLView

from ..schema import Query, schema
from . import JSON, HttpClient, Response


class GraphQLView(BaseGraphQLView):
    def get_root_value(self):
        return Query()


class SanicHttpClient(HttpClient):
    def __init__(self):
        self.app = Sanic(
            f"test_{int(randint(0, 1000))}",
            log_config={
                "version": 1,
                "loggers": {},
                "handlers": {},
            },
        )
        self.app.add_route(GraphQLView.as_view(schema=schema), "/graphql")

    async def post(self, url: str, json: JSON) -> Response:
        request, response = await self.app.asgi_client.post("/graphql", json=json)

        return Response(status_code=response.status_code, data=response.content)
