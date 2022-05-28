import json
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional

from typing_extensions import TypedDict

from graphql.error.graphql_error import format_error as format_graphql_error

from strawberry.exceptions import MissingQueryError
from strawberry.types import ExecutionResult


class GraphQLHTTPResponse(TypedDict, total=False):
    data: Optional[Dict[str, Any]]
    errors: Optional[List[Any]]
    extensions: Optional[Dict[str, Any]]


def process_result(result: ExecutionResult) -> GraphQLHTTPResponse:
    data: GraphQLHTTPResponse = {"data": result.data}

    if result.errors:
        data["errors"] = [format_graphql_error(err) for err in result.errors]
    if result.extensions:
        data["extensions"] = result.extensions

    return data


@dataclass
class GraphQLRequestData:
    query: str
    variables: Optional[Dict[str, Any]]
    operation_name: Optional[str]


def parse_query_params(params: Dict[str, str]) -> Dict[str, Any]:
    if "variables" in params:
        params["variables"] = json.loads(params["variables"])

    return params


def parse_request_data(data: Mapping) -> GraphQLRequestData:
    if "query" not in data:
        raise MissingQueryError()

    result = GraphQLRequestData(
        query=data["query"],
        variables=data.get("variables"),
        operation_name=data.get("operationName"),
    )

    return result
