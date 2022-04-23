import abc
from dataclasses import dataclass
from typing import Any, Dict, Optional


JSON = Dict[str, Any]


@dataclass
class Response:
    status_code: int
    data: bytes
    # TODO: headers

    @property
    def text(self) -> str:
        return self.data.decode()


class HttpClient(abc.ABC):
    @abc.abstractmethod
    def __init__(self, graphiql: bool = True):
        ...

    @abc.abstractmethod
    async def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> Response:
        ...

    @abc.abstractmethod
    async def post(
        self, url: str, json: JSON, headers: Optional[Dict[str, str]] = None
    ) -> Response:
        ...
