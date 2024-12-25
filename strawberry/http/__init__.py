from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from typing_extensions import Literal, TypedDict

if TYPE_CHECKING:
    from strawberry.types import ExecutionResult


class GraphQLHTTPResponse(TypedDict, total=False):
    data: dict[str, object] | None
    errors: list[object] | None
    extensions: dict[str, object] | None


def process_result(result: ExecutionResult) -> GraphQLHTTPResponse:
    data: GraphQLHTTPResponse = {"data": result.data}

    if result.errors:
        data["errors"] = [err.formatted for err in result.errors]
    if result.extensions:
        data["extensions"] = result.extensions

    return data


@dataclass
class GraphQLRequestData:
    # query is optional here as it can be added by an extensions
    # (for example an extension for persisted queries)
    query: str | None
    variables: dict[str, Any] | None
    operation_name: str | None
    protocol: Literal["http", "multipart-subscription"] = "http"


__all__ = [
    "GraphQLHTTPResponse",
    "GraphQLRequestData",
    "process_result",
]
