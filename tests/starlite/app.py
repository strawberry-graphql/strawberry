from tests.starlite.schema import schema

from starlite import Provide, Request, Starlite
from strawberry.starlite import make_graphql_controller
from strawberry.starlite.handlers.graphql_transport_ws_handler import (
    GraphQLTransportWSHandler,
)
from strawberry.starlite.handlers.graphql_ws_handler import GraphQLWSHandler


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


def custom_context_dependency() -> str:
    return "Hi!"


async def get_root_value(request: Request = None):
    return request


async def get_context(app_dependency: str, request: Request = None):
    return {
        "custom_value": app_dependency,
        "request": request,
    }


def create_app(schema=schema, **kwargs):

    GraphQLController = make_graphql_controller(
        schema,
        path="/graphql",
        context_getter=get_context,
        root_value_getter=get_root_value,
        **kwargs
    )

    class DebuggableGraphQLController(GraphQLController):
        graphql_ws_handler_class = DebuggableGraphQLWSHandler
        graphql_transport_ws_handler_class = DebuggableGraphQLTransportWSHandler

    app = Starlite(
        route_handlers=[DebuggableGraphQLController],
        dependencies={"app_dependency": Provide(custom_context_dependency)},
    )

    return app
