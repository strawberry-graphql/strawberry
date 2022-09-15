from typing import Any


def should_render_graphiql(graphiql: bool, request: Any) -> bool:
    if not graphiql:
        return False
    return any(
        supported_header in request.environ.get("HTTP_ACCEPT", "")
        for supported_header in ("text/html", "*/*")
    )
