from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from typing_extensions import Required, TypedDict

from graphql.error.graphql_error import format_error as format_graphql_error

from strawberry.exceptions import MissingQueryError
from strawberry.types import ExecutionResult


class GraphQLRequestData(TypedDict, total=False):
    query: Required[str]
    variables: Optional[Dict[str, Any]]
    operation_name: Optional[str]


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
class GraphQLRequest:
    query: str
    variables: Optional[Dict[str, Any]]
    operation_name: Optional[str]

    @classmethod
    def from_dict(cls, data: GraphQLRequestData) -> "GraphQLRequest":
        if "query" not in data:
            raise MissingQueryError()

        return GraphQLRequest(
            query=data["query"],
            variables=data.get("variables"),
            operation_name=data.get("operation_name"),
        )


def parse_request_data(
    data: Union[GraphQLRequestData, List[GraphQLRequestData]],
) -> Union[GraphQLRequest, List[GraphQLRequest]]:
    if isinstance(data, list):
        return [GraphQLRequest.from_dict(d) for d in data]

    return GraphQLRequest.from_dict(data)
