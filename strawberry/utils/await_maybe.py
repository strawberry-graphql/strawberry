import inspect
from collections.abc import AsyncIterator, Awaitable, Iterator
from typing import TypeAlias, TypeVar

T = TypeVar("T")

AwaitableOrValue: TypeAlias = Awaitable[T] | T
AsyncIteratorOrIterator: TypeAlias = AsyncIterator[T] | Iterator[T]


async def await_maybe(value: AwaitableOrValue[T]) -> T:
    if inspect.isawaitable(value):
        return await value

    return value


__all__ = ["AsyncIteratorOrIterator", "AwaitableOrValue", "await_maybe"]
