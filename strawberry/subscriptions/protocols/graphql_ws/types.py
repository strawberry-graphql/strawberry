from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from graphql import GraphQLFormattedError

from strawberry import UNSET
from strawberry.subscriptions.protocols.graphql_transport_ws.types import (
    GraphQLTransportMessage,
)

ConnectionInitPayload = Dict[str, Any]


ConnectionErrorPayload = Dict[str, Any]


@dataclass
class StartPayload(GraphQLTransportMessage):
    query: str
    variables: Optional[Dict[str, Any]] = UNSET
    operationName: Optional[str] = UNSET


@dataclass
class DataPayload(GraphQLTransportMessage):
    data: Any

    # Optional list of formatted graphql.GraphQLError objects
    errors: Optional[List[GraphQLFormattedError]] = UNSET


ErrorPayload = GraphQLFormattedError


OperationMessagePayload = Union[
    ConnectionInitPayload,
    ConnectionErrorPayload,
    StartPayload,
    DataPayload,
    ErrorPayload,
]


@dataclass
class OperationMessage(GraphQLTransportMessage):
    type: str
    id: str
    payload: OperationMessagePayload
