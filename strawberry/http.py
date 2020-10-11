from typing import Any, Dict, List, Optional

from typing_extensions import TypedDict

from graphql.error import format_error as format_graphql_error

from strawberry.types import ExecutionResult


class GraphQLHTTPResponse(TypedDict, total=False):
    data: Optional[Dict[str, Any]]
    errors: Optional[List[Any]]


def process_result(result: ExecutionResult) -> GraphQLHTTPResponse:
    data: GraphQLHTTPResponse = {"data": result.data}

    if result.errors:
        data["errors"] = [format_graphql_error(err) for err in result.errors]

    return data
