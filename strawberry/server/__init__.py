from starlette.applications import Starlette
from starlette.templating import Jinja2Templates
import uvicorn

import pathlib

from .graphql_app import GraphQLApp

import strawberry


@strawberry.type
class Query:
    hello: str = "World"


schema = strawberry.Schema(query=Query)


app = Starlette()

here = pathlib.Path(__file__).parent
templates_path = here / "templates"
templates = Jinja2Templates(directory=str(templates_path))

app = Starlette(debug=True)


@app.route("/")
async def homepage(request):
    return templates.TemplateResponse("playground.html", {"request": request})


app.add_route("/graphql", GraphQLApp(schema))


def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)
