import warnings
from typing_extensions import TypedDict

from sanic.request import Request
from strawberry.http.temporal_response import TemporalResponse


class StrawberrySanicContext(TypedDict):
    request: Request
    response: TemporalResponse

    # see https://github.com/python/mypy/issues/13066 for the type ignore
    def __getattr__(self, key: str) -> object:  # type: ignore
        # a warning will be raised because this is not supported anymore
        # but we need to keep it for backwards compatibility

        warnings.warn(
            "Accessing context attributes via the dot notation is deprecated, "
            "please use context.get('key') or context['key'] instead",
            DeprecationWarning,
            stacklevel=2,
        )

        return super().__getitem__(key)
