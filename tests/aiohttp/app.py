from aiohttp import web
from strawberry.aiohttp.views import GraphQLView
from tests.aiohttp.schema import Query, schema


def create_app(**kwargs):
    class MyGraphQLView(GraphQLView):
        async def get_root_value(self, request: web.Request):
            return Query()

    app = web.Application()
    app.router.add_route("*", "/graphql", MyGraphQLView(schema=schema, **kwargs))

    return app
