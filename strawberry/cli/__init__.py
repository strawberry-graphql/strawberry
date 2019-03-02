import click
import sys

import os
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
import importlib

import uvicorn

import hupper

from strawberry.contrib.starlette import GraphQLApp


@click.group()
def run():
    pass


@run.command("server")
@click.argument("module", type=str)
@click.option("-h", "--host", default="0.0.0.0", type=str)
@click.option("-p", "--port", default=8000, type=int)
def server(module, host, port):
    sys.path.append(os.getcwd())

    reloader = hupper.start_reloader("strawberry.cli.run", verbose=False)

    schema_module = importlib.import_module(module)

    reloader.watch_files([schema_module.__file__])

    app = Starlette(debug=True)
    app.add_route("/graphql", GraphQLApp(schema_module.schema))

    print(f"Running strawberry on http://{host}:{port}/graphql 🍓")

    uvicorn.run(app, host=host, port=port, log_level="error")
