from typing import Any

from aiohttp import web
from strawberry.aiohttp.handlers import GraphQLTransportWSHandler, GraphQLWSHandler
from strawberry.aiohttp.views import GraphQLView
from tests.views.schema import Query, schema


class DebuggableGraphQLTransportWSHandler(GraphQLTransportWSHandler):
    def get_tasks(self) -> list:
        return [op.task for op in self.operations.values()]

    async def get_context(self) -> object:
        context = await super().get_context()
        context["ws"] = self._ws
        context["get_tasks"] = self.get_tasks
        context["connectionInitTimeoutTask"] = self.connection_init_timeout_task
        return context


class DebuggableGraphQLWSHandler(GraphQLWSHandler):
    def get_tasks(self) -> list:
        return list(self.tasks.values())

    async def get_context(self) -> object:
        context = await super().get_context()
        context["ws"] = self._ws
        context["get_tasks"] = self.get_tasks
        context["connectionInitTimeoutTask"] = None
        return context


class MyGraphQLView(GraphQLView):
    graphql_transport_ws_handler_class = DebuggableGraphQLTransportWSHandler
    graphql_ws_handler_class = DebuggableGraphQLWSHandler

    async def get_root_value(self, request: web.Request) -> Query:
        await super().get_root_value(request)  # for coverage
        return Query()


def create_app(**kwargs: Any) -> web.Application:
    app = web.Application()
    app.router.add_route("*", "/graphql", MyGraphQLView(schema=schema, **kwargs))

    return app
