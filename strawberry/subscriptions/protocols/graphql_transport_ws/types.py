from typing import TypedDict, Union
from typing_extensions import Literal, NotRequired

from graphql import GraphQLFormattedError


class ConnectionInitMessage(TypedDict):
    """Direction: Client -> Server."""

    type: Literal["connection_init"]
    payload: NotRequired[Union[dict[str, object], None]]


class ConnectionAckMessage(TypedDict):
    """Direction: Server -> Client."""

    type: Literal["connection_ack"]
    payload: NotRequired[Union[dict[str, object], None]]


class PingMessage(TypedDict):
    """Direction: bidirectional."""

    type: Literal["ping"]
    payload: NotRequired[Union[dict[str, object], None]]


class PongMessage(TypedDict):
    """Direction: bidirectional."""

    type: Literal["pong"]
    payload: NotRequired[Union[dict[str, object], None]]


class SubscribeMessagePayload(TypedDict):
    operationName: NotRequired[Union[str, None]]
    query: str
    variables: NotRequired[Union[dict[str, object], None]]
    extensions: NotRequired[Union[dict[str, object], None]]


class SubscribeMessage(TypedDict):
    """Direction: Client -> Server."""

    id: str
    type: Literal["subscribe"]
    payload: SubscribeMessagePayload


class NextMessagePayload(TypedDict):
    errors: NotRequired[list[GraphQLFormattedError]]
    data: NotRequired[Union[dict[str, object], None]]
    extensions: NotRequired[dict[str, object]]


class NextMessage(TypedDict):
    """Direction: Server -> Client."""

    id: str
    type: Literal["next"]
    payload: NextMessagePayload


class ErrorMessage(TypedDict):
    """Direction: Server -> Client."""

    id: str
    type: Literal["error"]
    payload: list[GraphQLFormattedError]


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
    "CompleteMessage",
    "ConnectionAckMessage",
    "ConnectionInitMessage",
    "ErrorMessage",
    "Message",
    "NextMessage",
    "PingMessage",
    "PongMessage",
    "SubscribeMessage",
]
