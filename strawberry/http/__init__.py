from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional
from typing_extensions import Literal, TypedDict

from strawberry.schema._graphql_core import (
    GraphQLIncrementalExecutionResults,
    ResultType,
)


class GraphQLHTTPResponse(TypedDict, total=False):
    data: Optional[dict[str, object]]
    errors: Optional[list[object]]
    extensions: Optional[dict[str, object]]
    hasNext: Optional[bool]
    completed: Optional[list[Any]]
    pending: Optional[list[Any]]
    initial: Optional[list[Any]]
    incremental: Optional[list[Any]]


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
    query: Optional[str]
    variables: Optional[dict[str, Any]]
    operation_name: Optional[str]
    extensions: Optional[dict[str, Any]]
    protocol: Literal["http", "multipart-subscription"] = "http"


__all__ = [
    "GraphQLHTTPResponse",
    "GraphQLRequestData",
    "process_result",
]
