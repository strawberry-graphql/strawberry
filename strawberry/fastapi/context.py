from typing import Any, Dict, Optional, Union

from starlette.background import BackgroundTasks
from starlette.requests import Request
from starlette.responses import Response
from starlette.websockets import WebSocket

CustomContext = Union["BaseContext", Dict[str, Any]]
MergedContext = Union[
    "BaseContext", Dict[str, Union[Any, BackgroundTasks, Request, Response, WebSocket]]
]


class BaseContext:
    def __init__(self):
        self.request: Optional[Union[Request, WebSocket]] = None
        self.background_tasks: Optional[BackgroundTasks] = None
        self.response: Optional[Response] = None
        self.connection_params: Optional[Any] = None
