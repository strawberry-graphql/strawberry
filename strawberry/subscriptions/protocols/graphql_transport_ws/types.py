from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from strawberry.types.unset import UNSET

if TYPE_CHECKING:
    from graphql import GraphQLFormattedError


@dataclass
class GraphQLTransportMessage:
    def as_dict(self) -> dict:
        data = asdict(self)
        if getattr(self, "payload", None) is UNSET:
            # Unset fields must have a JSON value of "undefined" not "null"
            data.pop("payload")
        return data


@dataclass
class ConnectionInitMessage(GraphQLTransportMessage):
    """Direction: Client -> Server."""

    payload: Optional[Dict[str, Any]] = UNSET
    type: str = "connection_init"


@dataclass
class ConnectionAckMessage(GraphQLTransportMessage):
    """Direction: Server -> Client."""

    payload: Optional[Dict[str, Any]] = UNSET
    type: str = "connection_ack"


@dataclass
class PingMessage(GraphQLTransportMessage):
    """Direction: bidirectional."""

    payload: Optional[Dict[str, Any]] = UNSET
    type: str = "ping"


@dataclass
class PongMessage(GraphQLTransportMessage):
    """Direction: bidirectional."""

    payload: Optional[Dict[str, Any]] = UNSET
    type: str = "pong"


@dataclass
class SubscribeMessagePayload:
    query: str
    operationName: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    extensions: Optional[Dict[str, Any]] = None


@dataclass
class SubscribeMessage(GraphQLTransportMessage):
    """Direction: Client -> Server."""

    id: str
    payload: SubscribeMessagePayload
    type: str = "subscribe"


@dataclass
class NextMessage(GraphQLTransportMessage):
    """Direction: Server -> Client."""

    id: str
    payload: Dict[str, Any]  # TODO: shape like FormattedExecutionResult
    type: str = "next"

    def as_dict(self) -> dict:
        return {"id": self.id, "payload": self.payload, "type": self.type}


@dataclass
class ErrorMessage(GraphQLTransportMessage):
    """Direction: Server -> Client."""

    id: str
    payload: List[GraphQLFormattedError]
    type: str = "error"


@dataclass
class CompleteMessage(GraphQLTransportMessage):
    """Direction: bidirectional."""

    id: str
    type: str = "complete"


__all__ = [
    "ConnectionInitMessage",
    "ConnectionAckMessage",
    "PingMessage",
    "PongMessage",
    "SubscribeMessage",
    "NextMessage",
    "ErrorMessage",
    "CompleteMessage",
]
