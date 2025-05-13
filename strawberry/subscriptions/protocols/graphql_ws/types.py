from typing import TypedDict, Union
from typing_extensions import Literal, NotRequired

from graphql import GraphQLFormattedError


class ConnectionInitMessage(TypedDict):
    type: Literal["connection_init"]
    payload: NotRequired[dict[str, object]]


class StartMessagePayload(TypedDict):
    query: str
    variables: NotRequired[dict[str, object]]
    operationName: NotRequired[str]


class StartMessage(TypedDict):
    type: Literal["start"]
    id: str
    payload: StartMessagePayload


class StopMessage(TypedDict):
    type: Literal["stop"]
    id: str


class ConnectionTerminateMessage(TypedDict):
    type: Literal["connection_terminate"]


class ConnectionErrorMessage(TypedDict):
    type: Literal["connection_error"]
    payload: NotRequired[dict[str, object]]


class ConnectionAckMessage(TypedDict):
    type: Literal["connection_ack"]
    payload: NotRequired[dict[str, object]]


class DataMessagePayload(TypedDict):
    data: object
    errors: NotRequired[list[GraphQLFormattedError]]

    # Non-standard field:
    extensions: NotRequired[dict[str, object]]


class DataMessage(TypedDict):
    type: Literal["data"]
    id: str
    payload: DataMessagePayload


class ErrorMessage(TypedDict):
    type: Literal["error"]
    id: str
    payload: GraphQLFormattedError


class CompleteMessage(TypedDict):
    type: Literal["complete"]
    id: str


class ConnectionKeepAliveMessage(TypedDict):
    type: Literal["ka"]


OperationMessage = Union[
    ConnectionInitMessage,
    StartMessage,
    StopMessage,
    ConnectionTerminateMessage,
    ConnectionErrorMessage,
    ConnectionAckMessage,
    DataMessage,
    ErrorMessage,
    CompleteMessage,
    ConnectionKeepAliveMessage,
]


__all__ = [
    "CompleteMessage",
    "ConnectionAckMessage",
    "ConnectionErrorMessage",
    "ConnectionInitMessage",
    "ConnectionKeepAliveMessage",
    "ConnectionTerminateMessage",
    "DataMessage",
    "ErrorMessage",
    "OperationMessage",
    "StartMessage",
    "StopMessage",
]
