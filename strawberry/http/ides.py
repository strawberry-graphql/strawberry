import json
import pathlib
from typing import Literal

GraphQL_IDE = Literal["graphiql", "apollo-sandbox", "pathfinder"]


def get_graphql_ide_html(
    graphql_ide: GraphQL_IDE | None = "graphiql",
    subscription_url: str | None = None,
) -> str:
    here = pathlib.Path(__file__).parents[1]

    if graphql_ide == "apollo-sandbox":
        path = here / "static/apollo-sandbox.html"
    elif graphql_ide == "pathfinder":
        path = here / "static/pathfinder.html"
    else:
        path = here / "static/graphiql.html"

    html = path.read_text(encoding="utf-8")

    if graphql_ide == "graphiql" and subscription_url is not None:
        html = html.replace(
            "const customSubscriptionUrl = null;",
            f"const customSubscriptionUrl = {json.dumps(subscription_url)};",
        )

    return html


__all__ = ["GraphQL_IDE", "get_graphql_ide_html"]
