import os
from typing import Any

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware

from strawberry import Schema
from strawberry.asgi import GraphQL
from strawberry.cli.constants import (
    DEBUG_SERVER_LOG_OPERATIONS,
    DEBUG_SERVER_SCHEMA_ENV_VAR_KEY,
)
from strawberry.utils.importer import import_module_symbol

app = Starlette(debug=True)
app.add_middleware(
    CORSMiddleware, allow_headers=["*"], allow_origins=["*"], allow_methods=["*"]
)

schema_import_string = os.environ[DEBUG_SERVER_SCHEMA_ENV_VAR_KEY]
schema_symbol = import_module_symbol(schema_import_string, default_symbol_name="schema")
log_operations = os.environ[DEBUG_SERVER_LOG_OPERATIONS] == "True"

assert isinstance(schema_symbol, Schema)
graphql_app = GraphQL[Any, Any](schema_symbol, debug=log_operations)

paths = ["/", "/graphql"]
for path in paths:
    app.add_route(path, graphql_app)  # type: ignore
    app.add_websocket_route(path, graphql_app)  # type: ignore
