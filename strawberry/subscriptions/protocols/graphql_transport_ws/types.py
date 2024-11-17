from typing import Dict, List, TypedDict, Union
from typing_extensions import Literal, NotRequired

from graphql import GraphQLFormattedError


class ConnectionInitMessage(TypedDict):
    """Direction: Client -> Server."""

    type: Literal["connection_init"]
    payload: NotRequired[Union[Dict[str, object], None]]


class ConnectionAckMessage(TypedDict):
    """Direction: Server -> Client."""

    type: Literal["connection_ack"]
    payload: NotRequired[Union[Dict[str, object], None]]


class PingMessage(TypedDict):
    """Direction: bidirectional."""

    type: Literal["ping"]
    payload: NotRequired[Union[Dict[str, object], None]]


class PongMessage(TypedDict):
    """Direction: bidirectional."""

    type: Literal["pong"]
    payload: NotRequired[Union[Dict[str, object], None]]


class SubscribeMessagePayload(TypedDict):
    operationName: NotRequired[Union[str, None]]
    query: str
    variables: NotRequired[Union[Dict[str, object], None]]
    extensions: NotRequired[Union[Dict[str, object], None]]


class SubscribeMessage(TypedDict):
    """Direction: Client -> Server."""

    id: str
    type: Literal["subscribe"]
    payload: SubscribeMessagePayload


class NextMessagePayload(TypedDict):
    errors: NotRequired[List[GraphQLFormattedError]]
    data: NotRequired[Union[Dict[str, object], None]]
    extensions: NotRequired[Dict[str, object]]


class NextMessage(TypedDict):
    """Direction: Server -> Client."""

    id: str
    type: Literal["next"]
    payload: NextMessagePayload


class ErrorMessage(TypedDict):
    """Direction: Server -> Client."""

    id: str
    type: Literal["error"]
    payload: List[GraphQLFormattedError]


class CompleteMessage(TypedDict):
    """Direction: bidirectional."""

    id: str
    type: Literal["complete"]


Message = Union[
    ConnectionInitMessage,
    ConnectionAckMessage,
    PingMessage,
    PongMessage,
    SubscribeMessage,
    NextMessage,
    ErrorMessage,
    CompleteMessage,
]


__all__ = [
    "ConnectionInitMessage",
    "ConnectionAckMessage",
    "PingMessage",
    "PongMessage",
    "SubscribeMessage",
    "NextMessage",
    "ErrorMessage",
    "CompleteMessage",
    "Message",
]
