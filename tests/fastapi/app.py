from fastapi import BackgroundTasks, Depends, FastAPI, Request, WebSocket
from strawberry.fastapi import GraphQLRouter as BaseGraphQLRouter
from strawberry.fastapi.handlers import GraphQLTransportWSHandler, GraphQLWSHandler
from tests.fastapi.schema import schema


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


async def get_context(
    background_tasks: BackgroundTasks,
    request: Request = None,
    ws: WebSocket = None,
    custom_value=Depends(custom_context_dependency),
):
    return {
        "custom_value": custom_value,
        "request": request or ws,
        "background_tasks": background_tasks,
    }


async def get_root_value(request: Request = None, ws: WebSocket = None):
    return request or ws


class GraphQLRouter(BaseGraphQLRouter):
    graphql_transport_ws_handler_class = DebuggableGraphQLTransportWSHandler
    graphql_ws_handler_class = DebuggableGraphQLWSHandler


def create_app(schema=schema, **kwargs):
    app = FastAPI()

    graphql_app = GraphQLRouter(
        schema, context_getter=get_context, root_value_getter=get_root_value, **kwargs
    )
    app.include_router(graphql_app, prefix="/graphql")

    return app
