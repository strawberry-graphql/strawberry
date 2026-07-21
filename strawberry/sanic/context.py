from typing_extensions import TypedDict

from sanic.request import Request

from strawberry.http.temporal_response import TemporalResponse


class StrawberrySanicContext(TypedDict):
    request: Request
    response: TemporalResponse


__all__ = ["StrawberrySanicContext"]
