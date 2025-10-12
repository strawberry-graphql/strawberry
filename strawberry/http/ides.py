import pathlib
from typing import Literal

_BASE_DIR = pathlib.Path(__file__).parents[1]

GraphQL_IDE = Literal["graphiql", "apollo-sandbox", "pathfinder"]


def get_graphql_ide_html(
    graphql_ide: GraphQL_IDE | None = "graphiql",
) -> str:
    if graphql_ide == "apollo-sandbox":
        path = _BASE_DIR / "static/apollo-sandbox.html"
    elif graphql_ide == "pathfinder":
        path = _BASE_DIR / "static/pathfinder.html"
    else:
        path = _BASE_DIR / "static/graphiql.html"

    return path.read_text(encoding="utf-8")


__all__ = ["GraphQL_IDE", "get_graphql_ide_html"]
