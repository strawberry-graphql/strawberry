from typing import Dict, List, TypedDict, Union
from typing_extensions import Literal, NotRequired

from graphql import GraphQLFormattedError


class ConnectionInitMessage(TypedDict):
    type: Literal["connection_init"]
    payload: NotRequired[Dict[str, object]]


class StartMessagePayload(TypedDict):
    query: str
    variables: NotRequired[Dict[str, object]]
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
    payload: NotRequired[Dict[str, object]]


class ConnectionAckMessage(TypedDict):
    type: Literal["connection_ack"]


class DataMessagePayload(TypedDict):
    data: object
    errors: NotRequired[List[GraphQLFormattedError]]

    # Non-standard field:
    extensions: NotRequired[Dict[str, object]]


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
    "ConnectionInitMessage",
    "StartMessage",
    "StopMessage",
    "ConnectionTerminateMessage",
    "ConnectionErrorMessage",
    "ConnectionAckMessage",
    "DataMessage",
    "ErrorMessage",
    "CompleteMessage",
    "ConnectionKeepAliveMessage",
    "OperationMessage",
]
