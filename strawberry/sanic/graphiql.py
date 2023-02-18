from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sanic.request import Request


def should_render_graphiql(graphiql: bool, request: Request) -> bool:
    if not graphiql:
        return False
    return any(
        supported_header in request.headers.get("accept", "")
        for supported_header in ("text/html", "*/*")
    )
