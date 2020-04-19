import pathlib


def get_graphiql_html(request_path: str) -> str:
    here = pathlib.Path(__file__).parents[1]
    path = here / "static/graphiql.html"

    with open(path) as f:
        template = f.read()

    return template.replace("{{REQUEST_PATH}}", request_path)
