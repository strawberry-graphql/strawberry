import click
import sys

import os
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware

import importlib

import uvicorn

import hupper

from strawberry.asgi import GraphQL


@click.command("server", short_help='Starts debug server')
@click.argument("module", type=str)
@click.option("-h", "--host", default="0.0.0.0", type=str)
@click.option("-p", "--port", default=8000, type=int)
def server(module, host, port):
    sys.path.append(os.getcwd())

    reloader = hupper.start_reloader("strawberry.cli.run", verbose=False)

    schema_module = importlib.import_module(module)

    reloader.watch_files([schema_module.__file__])

    app = Starlette(debug=True)

    app.add_middleware(
        CORSMiddleware, allow_headers=["*"], allow_origins=["*"], allow_methods=["*"]
    )

    graphql_app = GraphQL(schema_module.schema, debug=True)

    app.add_route("/graphql", graphql_app)
    app.add_websocket_route("/graphql", graphql_app)

    print(f"Running strawberry on http://{host}:{port}/graphql 🍓")

    uvicorn.run(app, host=host, port=port, log_level="error")
