from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Optional
from typing_extensions import TypedDict

if TYPE_CHECKING:
    from strawberry.types import ExecutionResult


class GraphQLHTTPResponse(TypedDict, total=False):
    data: Optional[Dict[str, object]]
    errors: Optional[List[object]]
    extensions: Optional[Dict[str, object]]


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
    query: Optional[str]
    variables: Optional[Dict[str, Any]]
    operation_name: Optional[str]


def parse_query_params(params: Dict[str, str]) -> Dict[str, Any]:
    if "variables" in params:
        params["variables"] = json.loads(params["variables"])

    return params


def parse_request_data(data: Mapping[str, Any]) -> GraphQLRequestData:
    return GraphQLRequestData(
        query=data.get("query"),
        variables=data.get("variables"),
        operation_name=data.get("operationName"),
    )
