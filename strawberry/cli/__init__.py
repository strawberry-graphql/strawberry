import click
import sys

import os
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
import importlib

import uvicorn

import pathlib
import hupper

from strawberry.contrib.starlette import GraphQLApp


app = Starlette()

here = pathlib.Path(__file__).parent
templates_path = here / "templates"

app = Starlette(debug=True)


@app.route("/")
async def homepage(request):
    with open(templates_path / "playground.html") as f:
        template = f.read()

    return HTMLResponse(template)


@click.group()
def run():
    pass


@run.command("server")
@click.argument("module", type=str)
def server(module):
    sys.path.append(os.getcwd())

    reloader = hupper.start_reloader("strawberry.cli.run")

    schema_module = importlib.import_module(module)

    reloader.watch_files([schema_module.__file__])

    app.add_route("/graphql", GraphQLApp(schema_module.schema))
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")
