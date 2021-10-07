from aiohttp import web
from strawberry.aiohttp.handlers import GraphQLTransportWSHandler, GraphQLWSHandler
from strawberry.aiohttp.views import GraphQLView
from tests.aiohttp.schema import Query, schema


class DebuggableGraphQLTransportWSHandler(GraphQLTransportWSHandler):
    async def get_context(self) -> object:
        context = await super().get_context()
        context["ws"] = self._ws
        context["tasks"] = self.tasks
        context["connectionInitTimeoutTask"] = self.connection_init_timeout_task
        return context


class DebuggableGraphQLWSHandler(GraphQLWSHandler):
    async def get_context(self) -> object:
        context = await super().get_context()
        context["ws"] = self._ws
        context["tasks"] = self.tasks
        context["connectionInitTimeoutTask"] = None
        return context


class MyGraphQLView(GraphQLView):
    graphql_transport_ws_handler_class = DebuggableGraphQLTransportWSHandler
    graphql_ws_handler_class = DebuggableGraphQLWSHandler

    async def get_root_value(self, request: web.Request):
        return Query()


def create_app(**kwargs):
    app = web.Application()
    app.router.add_route("*", "/graphql", MyGraphQLView(schema=schema, **kwargs))

    return app
