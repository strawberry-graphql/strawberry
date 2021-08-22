import inspect
from typing import Union, Awaitable, TypeVar


T = TypeVar("T")

AwaitableOrValue = Union[Awaitable[T], T]


async def await_maybe(value: AwaitableOrValue):
    if inspect.iscoroutine(value):
        return await value

    return value
