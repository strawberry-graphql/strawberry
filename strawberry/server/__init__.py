import click

from starlette.applications import Starlette
from starlette.templating import Jinja2Templates
import importlib

import uvicorn

import pathlib
import hupper

from .graphql_app import GraphQLApp


app = Starlette()

here = pathlib.Path(__file__).parent
templates_path = here / "templates"
templates = Jinja2Templates(directory=str(templates_path))

app = Starlette(debug=True)


@app.route("/")
async def homepage(request):
    return templates.TemplateResponse("playground.html", {"request": request})


@click.command()
@click.argument("module")
def main(module):

    reloaded = hupper.start_reloader("strawberry.server.main")
    schema_module = importlib.import_module(module)

    reloaded.watch_files([schema_module.__file__])

    app.add_route("/graphql", GraphQLApp(schema_module.schema))
    uvicorn.run(app, host="0.0.0.0", port=8000)
