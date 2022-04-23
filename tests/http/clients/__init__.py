import abc
from dataclasses import dataclass
from typing import Any, Dict


JSON = Dict[str, Any]


@dataclass
class Response:
    status_code: int
    data: bytes
    # TODO: headers


class HttpClient(abc.ABC):
    @abc.abstractmethod
    async def post(self, url: str, json: JSON) -> Response:
        ...
