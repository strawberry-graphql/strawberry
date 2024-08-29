from typing import Any, Dict, List, Optional, Union
from typing_extensions import TypedDict

from graphql import GraphQLFormattedError

ConnectionInitPayload = Dict[str, Any]


ConnectionErrorPayload = Dict[str, Any]


class StartPayload(TypedDict, total=False):
    query: str
    variables: Optional[Dict[str, Any]]
    operationName: Optional[str]


class DataPayload(TypedDict, total=False):
    data: Any

    # Optional list of formatted graphql.GraphQLError objects
    errors: Optional[List[GraphQLFormattedError]]


ErrorPayload = GraphQLFormattedError


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


__all__ = [
    "ConnectionInitPayload",
    "ConnectionErrorPayload",
    "StartPayload",
    "DataPayload",
    "ErrorPayload",
    "OperationMessagePayload",
    "OperationMessage",
]
