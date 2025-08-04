from lia import HTTPException


# WebSocket-specific exceptions that remain in Strawberry
class NonTextMessageReceived(Exception):
    pass


class NonJsonMessageReceived(Exception):
    pass


class WebSocketDisconnected(Exception):
    pass


__all__ = [
    "HTTPException",
    "NonJsonMessageReceived",
    "NonTextMessageReceived",
    "WebSocketDisconnected",
]
