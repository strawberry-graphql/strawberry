import sys
from typing import Any, Callable, TypeVar


if sys.version_info < (3, 8):
    from backports.cached_property import cached_property as _cached_property
else:
    from functools import cached_property as _cached_property

T = TypeVar("T")


def cached_property(func: Callable[[Any], T]) -> _cached_property[T]:
    """Helper to return the cached_property from functools or backports."""
    return _cached_property(func)
