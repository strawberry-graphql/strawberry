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


def process_result(result: ResultType) -> GraphQLHTTPResponse:
    if isinstance(result, GraphQLIncrementalExecutionResults):
        return result

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
    query: Optional[str]
    variables: Optional[dict[str, Any]]
    operation_name: Optional[str]
    protocol: Literal["http", "multipart-subscription"] = "http"


__all__ = [
    "GraphQLHTTPResponse",
    "GraphQLRequestData",
    "process_result",
]
