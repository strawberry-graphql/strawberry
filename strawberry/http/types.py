from typing import Any, Mapping, Optional
from typing_extensions import Literal, TypedDict

HTTPMethod = Literal[
    "GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE"
]

QueryParams = Mapping[str, Optional[str]]


class FormData(TypedDict):
    files: Mapping[str, Any]
    form: Mapping[str, Any]


__all__ = ["HTTPMethod", "QueryParams", "FormData"]
