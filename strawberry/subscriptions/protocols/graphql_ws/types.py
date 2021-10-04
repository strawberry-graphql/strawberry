from typing import Any, Dict, List, Optional, Union

from typing_extensions import TypedDict


ConnectionInitPayload = Dict[str, Any]


ConnectionErrorPayload = Dict[str, Any]


class StartPayload(TypedDict, total=False):
    query: str
    variables: Optional[Dict[str, Any]]
    operationName: Optional[str]


class DataPayload(TypedDict, total=False):
    data: Any

    # Optional list of formatted graphql.GraphQLError objects
    errors: Optional[List[Dict[str, Any]]]


class ErrorPayload(TypedDict):
    id: str

    # Formatted graphql.GraphQLError object
    payload: Dict[str, Any]


OperationMessagePayload = Union[
    ConnectionInitPayload,
    ConnectionErrorPayload,
    StartPayload,
    DataPayload,
    ErrorPayload,
]


class OperationMessage(TypedDict, total=False):
    type: str
    id: str
    payload: OperationMessagePayload
