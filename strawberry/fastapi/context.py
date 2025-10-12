from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from starlette.background import BackgroundTasks
    from starlette.requests import Request
    from starlette.responses import Response
    from starlette.websockets import WebSocket

CustomContext = "BaseContext | dict[str, Any]"
MergedContext = (
    "BaseContext | dict[str, Any | BackgroundTasks | Request | Response | WebSocket]"
)


class BaseContext:
    connection_params: Any | None = None

    def __init__(self) -> None:
        self.request: Request | WebSocket | None = None
        self.background_tasks: BackgroundTasks | None = None
        self.response: Response | None = None


__all__ = ["BaseContext"]
