from typing_extensions import TypedDict

from sanic.request import Request
from strawberry.http.temporal_response import TemporalResponse


class StrawberrySanicContext(TypedDict):
    request: Request
    response: TemporalResponse

    # see https://github.com/python/mypy/issues/13066 for the type ignore
    def __getattr__(self, key: str) -> object:  # type: ignore
        # TODO: raise a warning?
        return super().__getitem__(key)
