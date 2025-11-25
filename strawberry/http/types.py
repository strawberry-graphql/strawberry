from collections.abc import Mapping
from typing import Any, Literal
from typing_extensions import TypedDict

HTTPMethod = Literal[
    "GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE"
]

QueryParams = Mapping[str, str | None]


class FormData(TypedDict):
    files: Mapping[str, Any]
    form: Mapping[str, Any]


__all__ = ["FormData", "HTTPMethod", "QueryParams"]
