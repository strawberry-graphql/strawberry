from typing import Any

from starlite import Provide, Request, Starlite
from strawberry.starlite import make_graphql_controller
from tests.starlite.schema import schema


def custom_context_dependency() -> str:
    return "Hi!"


async def get_root_value(request: Request = None):
    return request


async def get_context(app_dependency: str, request: Request = None):
    return {
        "custom_value": app_dependency,
        "request": request,
    }


def create_app(schema=schema, **kwargs: Any):
    GraphQLController = make_graphql_controller(
        schema,
        path="/graphql",
        context_getter=get_context,
        root_value_getter=get_root_value,
        **kwargs,
    )

    app = Starlite(
        route_handlers=[GraphQLController],
        dependencies={"app_dependency": Provide(custom_context_dependency)},
    )

    return app
