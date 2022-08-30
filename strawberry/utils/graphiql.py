import json
import pathlib


def get_graphiql_html(
    subscription_enabled: bool = True, replace_variables: bool = True
) -> str:
    here = pathlib.Path(__file__).parents[1]
    path = here / "static/graphiql.html"

    template = path.read_text(encoding="utf-8")

    if replace_variables:
        template = template.replace(
            "{{ SUBSCRIPTION_ENABLED }}", json.dumps(subscription_enabled)
        )

    return template
