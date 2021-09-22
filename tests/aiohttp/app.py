from aiohttp import web
from strawberry.aiohttp.handlers import GraphQLTransportWSHandler
from strawberry.aiohttp.views import GraphQLView
from tests.aiohttp.schema import Query, schema


class DebuggableGraphQLTransportWSHandler(GraphQLTransportWSHandler):
    async def get_context(self) -> object:
        context = await super().get_context()
        context["tasks"] = self.tasks
        context["connectionInitTimeoutTask"] = self.connection_init_timeout_task
        return context


# TODO: move the other protocols debuggable handler here as well


def create_app(**kwargs):
    class MyGraphQLView(GraphQLView):
        graphql_transport_ws_handler_class = DebuggableGraphQLTransportWSHandler

        async def get_root_value(self, request: web.Request):
            return Query()

    app = web.Application()
    app.router.add_route("*", "/graphql", MyGraphQLView(schema=schema, **kwargs))

    return app
