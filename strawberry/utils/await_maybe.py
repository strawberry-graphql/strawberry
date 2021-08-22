import inspect
from typing import Callable


async def await_maybe(function: Callable):
    if inspect.iscoroutinefunction(function):
        return await function()

    return function()
