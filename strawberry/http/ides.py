import json
import pathlib
from typing_extensions import Literal

GraphQL_IDE = Literal["graphiql", "apollo-sandbox"]


def get_graphql_ide_html(
    subscription_enabled: bool = True,
    replace_variables: bool = True,
    graphql_ide: GraphQL_IDE = "graphiql",
) -> str:
    here = pathlib.Path(__file__).parents[1]

    if graphql_ide == "apollo-sandbox":
        path = here / "static/apollo-sandbox.html"
    else:
        path = here / "static/graphiql.html"

    template = path.read_text(encoding="utf-8")

    if replace_variables:
        template = template.replace(
            "{{ SUBSCRIPTION_ENABLED }}", json.dumps(subscription_enabled)
        )

    return template
