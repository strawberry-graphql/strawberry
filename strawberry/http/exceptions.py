class HTTPException(Exception):
    def __init__(self, status_code: int, reason: str) -> None:
        self.status_code = status_code
        self.reason = reason


class NonJsonMessageReceived(Exception):
    pass


__all__ = ["HTTPException"]
