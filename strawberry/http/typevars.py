from typing_extensions import TypeVar

Request = TypeVar("Request", contravariant=True)  # noqa: PLC0105
Response = TypeVar("Response")
SubResponse = TypeVar("SubResponse")
WebSocketRequest = TypeVar("WebSocketRequest")
WebSocketResponse = TypeVar("WebSocketResponse")
Context = TypeVar("Context", default=None)
RootValue = TypeVar("RootValue", default=None)


__all__ = [
    "Context",
    "Request",
    "Response",
    "RootValue",
    "SubResponse",
    "WebSocketRequest",
    "WebSocketResponse",
]
