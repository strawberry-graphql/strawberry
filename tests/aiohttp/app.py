from typing import Any

from aiohttp import web
from strawberry.aiohttp.views import GraphQLView
from tests.views.schema import Query, schema


class MyGraphQLView(GraphQLView):
    async def get_root_value(self, request: web.Request) -> Query:
        await super().get_root_value(request)  # for coverage
        return Query()


def create_app(**kwargs: Any) -> web.Application:
    app = web.Application()
    app.router.add_route("*", "/graphql", MyGraphQLView(schema=schema, **kwargs))

    return app
