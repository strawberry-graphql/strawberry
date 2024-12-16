from typing import TypeVar

Request = TypeVar("Request", contravariant=True)
Response = TypeVar("Response")
SubResponse = TypeVar("SubResponse")
WebSocketRequest = TypeVar("WebSocketRequest")
WebSocketResponse = TypeVar("WebSocketResponse")
Context = TypeVar("Context")
RootValue = TypeVar("RootValue")


__all__ = [
    "Context",
    "Request",
    "Response",
    "RootValue",
    "SubResponse",
    "WebSocketRequest",
    "WebSocketResponse",
]
