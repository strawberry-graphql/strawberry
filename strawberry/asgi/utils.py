import pathlib


def get_graphiql_html() -> str:
    here = pathlib.Path(__file__).parents[1]
    path = here / "static/graphiql.html"

    with open(path) as f:
        template = f.read()

    return template.replace("{{ SUBSCRIPTION_ENABLED }}", "true")
