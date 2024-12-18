import inspect
from collections.abc import AsyncIterator, Awaitable, Iterator
from typing import TypeVar, Union

T = TypeVar("T")

AwaitableOrValue = Union[Awaitable[T], T]
AsyncIteratorOrIterator = Union[AsyncIterator[T], Iterator[T]]


async def await_maybe(value: AwaitableOrValue[T]) -> T:
    if inspect.isawaitable(value):
        return await value

    return value


__all__ = ["AsyncIteratorOrIterator", "AwaitableOrValue", "await_maybe"]
