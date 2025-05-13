class HTTPException(Exception):
    def __init__(self, status_code: int, reason: str) -> None:
        self.status_code = status_code
        self.reason = reason


class NonTextMessageReceived(Exception):
    pass


class NonJsonMessageReceived(Exception):
    pass


class WebSocketDisconnected(Exception):
    pass


__all__ = ["HTTPException"]
