import os
from typing import Any

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import BaseRoute, Route, WebSocketRoute

from strawberry import Schema
from strawberry.asgi import GraphQL
from strawberry.cli.constants import DEV_SERVER_SCHEMA_ENV_VAR_KEY
from strawberry.utils.importer import import_module_symbol

schema_import_string = os.environ[DEV_SERVER_SCHEMA_ENV_VAR_KEY]
schema_symbol = import_module_symbol(schema_import_string, default_symbol_name="schema")

assert isinstance(schema_symbol, Schema)
graphql_app = GraphQL[Any, Any](schema_symbol)

paths = ["/", "/graphql"]
routes: list[BaseRoute] = []
for path in paths:
    routes.append(Route(path, graphql_app))
    routes.append(WebSocketRoute(path, graphql_app))

app = Starlette(debug=True, routes=routes)
app.add_middleware(
    CORSMiddleware, allow_headers=["*"], allow_origins=["*"], allow_methods=["*"]
)
