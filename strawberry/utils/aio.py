import sys
from typing import (
    Any,
    AsyncGenerator,
    AsyncIterable,
    AsyncIterator,
    Awaitable,
    Callable,
    List,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

_T = TypeVar("_T")
_R = TypeVar("_R")


async def aenumerate(
    iterable: Union[AsyncIterator[_T], AsyncIterable[_T]],
) -> AsyncIterator[Tuple[int, _T]]:
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

    try:
        async for i, element in aenumerate(aiterable):
            if i == nexti:
                yield element
                nexti = next(it)
    except StopIteration:
        return


async def asyncgen_to_list(generator: AsyncGenerator[_T, Any]) -> List[_T]:
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
