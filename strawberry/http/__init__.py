from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal
from typing_extensions import TypedDict

from strawberry.schema._graphql_core import (
    GraphQLIncrementalExecutionResults,
    ResultType,
)


class GraphQLHTTPResponse(TypedDict, total=False):
    data: dict[str, object] | None
    errors: list[object] | None
    extensions: dict[str, object] | None
    hasNext: bool | None
    completed: list[Any] | None
    pending: list[Any] | None
    initial: list[Any] | None
    incremental: list[Any] | None


def process_result(result: ResultType) -> GraphQLHTTPResponse:
    if isinstance(result, GraphQLIncrementalExecutionResults):
        return result

    errors, extensions = result.errors, result.extensions
    data: GraphQLHTTPResponse = {
        "data": result.data,
        **({"errors": [err.formatted for err in errors]} if errors else {}),
        **({"extensions": extensions} if extensions else {}),
    }

    return data


@dataclass
class GraphQLRequestData:
    # query is optional here as it can be added by an extensions
    # (for example an extension for persisted queries)
    query: str | None
    variables: dict[str, Any] | None
    operation_name: str | None
    extensions: dict[str, Any] | None
    protocol: Literal["http", "multipart-subscription"] = "http"


__all__ = [
    "GraphQLHTTPResponse",
    "GraphQLRequestData",
    "process_result",
]
