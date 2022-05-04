from dataclasses import dataclass

from sanic.request import Request
from strawberry.http.temporal_response import TemporalResponse


@dataclass
class StrawberrySanicContext:
    request: Request
    response: TemporalResponse

    def __getitem__(self, key):
        return super().__getattribute__(key)
