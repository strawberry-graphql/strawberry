from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional, Union
from typing_extensions import Literal, NotRequired, TypedDict

from strawberry.types import InitialIncrementalExecutionResult

if TYPE_CHECKING:
    from strawberry.types import ExecutionResult


class GraphQLHTTPResponse(TypedDict, total=False):
    data: Optional[dict[str, object]]
    errors: Optional[list[object]]
    extensions: Optional[dict[str, object]]


def process_result(
    result: Union[ExecutionResult, InitialIncrementalExecutionResult],
) -> GraphQLHTTPResponse:
    data: GraphQLHTTPResponse = {"data": result.data}

    if result.errors:
        data["errors"] = [err.formatted for err in result.errors]
    if result.extensions:
        data["extensions"] = result.extensions

    if isinstance(result, InitialIncrementalExecutionResult):
        data["hasNext"] = result.has_next
        data["pending"] = result.pending

    return data


@dataclass
class GraphQLRequestData:
    # query is optional here as it can be added by an extensions
    # (for example an extension for persisted queries)
    query: Optional[str]
    variables: Optional[dict[str, Any]]
    operation_name: Optional[str]
    protocol: Literal["http", "multipart-subscription"] = "http"


class IncrementalGraphQLHTTPResponse(TypedDict):
    incremental: list[GraphQLHTTPResponse]
    hasNext: bool
    extensions: NotRequired[dict[str, Any]]
    completed: list[GraphQLHTTPResponse]


__all__ = [
    "GraphQLHTTPResponse",
    "GraphQLRequestData",
    "IncrementalGraphQLHTTPResponse",
    "process_result",
]
