from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Union

from graphql import GraphQLFormattedError

from strawberry import UNSET
from strawberry.subscriptions.protocols.graphql_transport_ws.types import (
    GraphQLTransportMessage,
)

ConnectionInitPayload = Dict[str, Any]


ConnectionErrorPayload = Dict[str, Any]


@dataclass
class GraphQLTransportMessage:
    def as_dict(self) -> dict:
        data = asdict(self)
        if getattr(self, "payload", None) is UNSET:
            # Unset fields must have a JSON value of "undefined" not "null"
            data.pop("payload")
        return data


@dataclass
class StartPayload(GraphQLTransportMessage):
    query: str
    variables: Optional[Dict[str, Any]] = field(default_factory=dict[str, Any])
    operationName: Optional[str] = None


@dataclass
class DataPayload:
    data: Any

    # Optional list of formatted graphql.GraphQLError objects
    errors: Optional[List[GraphQLFormattedError]] = field(
        default_factory=list[GraphQLFormattedError]
    )


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
    id: Optional[str] = ""
    payload: Optional[OperationMessagePayload] = None
