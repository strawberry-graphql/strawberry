class NonTextMessageReceived(Exception):
    pass


class NonJsonMessageReceived(Exception):
    pass


class WebSocketDisconnected(Exception):
    pass


__all__ = [
    "NonJsonMessageReceived",
    "NonTextMessageReceived",
    "WebSocketDisconnected",
]
