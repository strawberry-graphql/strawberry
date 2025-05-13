import pathlib
from typing import Optional
from typing_extensions import Literal

GraphQL_IDE = Literal["graphiql", "apollo-sandbox", "pathfinder"]


def get_graphql_ide_html(
    graphql_ide: Optional[GraphQL_IDE] = "graphiql",
) -> str:
    here = pathlib.Path(__file__).parents[1]

    if graphql_ide == "apollo-sandbox":
        path = here / "static/apollo-sandbox.html"
    elif graphql_ide == "pathfinder":
        path = here / "static/pathfinder.html"
    else:
        path = here / "static/graphiql.html"

    return path.read_text(encoding="utf-8")


__all__ = ["GraphQL_IDE", "get_graphql_ide_html"]
