import inspect
from typing import AsyncIterator, Awaitable, Iterator, TypeVar, Union, cast

T = TypeVar("T")

AwaitableOrValue = Union[Awaitable[T], T]
AsyncIteratorOrIterator = Union[AsyncIterator[T], Iterator[T]]


async def await_maybe(value: AwaitableOrValue[T]) -> T:
    if inspect.isawaitable(value):
        return await value

    return cast(T, value)
