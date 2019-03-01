import click

from starlette.applications import Starlette
from starlette.templating import Jinja2Templates
import importlib

import uvicorn

import pathlib

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
    schema = importlib.import_module(module).schema

    app.add_route("/graphql", GraphQLApp(schema))
    uvicorn.run(app, host="0.0.0.0", port=8000)
