import inspect


async def await_maybe(value):
    if inspect.iscoroutine(value):
        return await value
    return value
