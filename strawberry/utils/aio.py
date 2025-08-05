import sys
from collections.abc import AsyncGenerator, AsyncIterable, AsyncIterator, Awaitable
from contextlib import asynccontextmanager, suppress
from typing import (
    Any,
    Callable,
    Optional,
    TypeVar,
    Union,
    cast,
)

_T = TypeVar("_T")
_R = TypeVar("_R")


@asynccontextmanager
async def aclosing(thing: _T) -> AsyncGenerator[_T, None]:
    """Ensure that an async generator is closed properly.

    Port from the stdlib contextlib.asynccontextmanager. Can be removed
    and replaced with the stdlib version when we drop support for Python
    versions before 3.10.
    """
    try:
        yield thing
    finally:
        with suppress(Exception):
            await cast("AsyncGenerator", thing).aclose()


async def aenumerate(
    iterable: Union[AsyncIterator[_T], AsyncIterable[_T]],
) -> AsyncIterator[tuple[int, _T]]:
    """Async version of enumerate."""
    i = 0
    async for element in iterable:
        yield i, element
        i += 1


async def aislice(
    aiterable: Union[AsyncIterator[_T], AsyncIterable[_T]],
    start: Optional[int] = None,
    stop: Optional[int] = None,
    step: Optional[int] = None,
) -> AsyncIterator[_T]:
    """Async version of itertools.islice."""
    # This is based on
    it = iter(
        range(
            start if start is not None else 0,
            stop if stop is not None else sys.maxsize,
            step if step is not None else 1,
        )
    )
    try:
        nexti = next(it)
    except StopIteration:
        return

    i = 0
    try:
        async for element in aiterable:
            if i == nexti:
                yield element
                nexti = next(it)
            i += 1
    except StopIteration:
        return


async def asyncgen_to_list(generator: AsyncGenerator[_T, Any]) -> list[_T]:
    """Convert an async generator to a list."""
    return [element async for element in generator]


async def resolve_awaitable(
    awaitable: Awaitable[_T],
    callback: Callable[[_T], _R],
) -> _R:
    """Resolves an awaitable object and calls a callback with the resolved value."""
    return callback(await awaitable)


__all__ = [
    "aenumerate",
    "aislice",
    "asyncgen_to_list",
    "resolve_awaitable",
]
