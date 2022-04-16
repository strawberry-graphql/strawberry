from os.path import abspath, dirname, join
from typing import Any


def render_graphiql_page() -> str:
    dir_path = abspath(join(dirname(__file__), ".."))
    graphiql_html_file = f"{dir_path}/static/graphiql.html"

    html_string = None

    with open(graphiql_html_file, "r") as f:
        html_string = f.read()

    return html_string.replace("{{ SUBSCRIPTION_ENABLED }}", "false")


def should_render_graphiql(graphiql: bool, request: Any) -> bool:
    if not graphiql:
        return False
    return any(
        supported_header in request.environ.get("HTTP_ACCEPT", "")
        for supported_header in ("text/html", "*/*")
    )
