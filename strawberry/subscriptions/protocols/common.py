from inspect import isawaitable
from typing import Any, AsyncIterator, Callable


# The following method can be employed until graphql core implements a better
# itererator object.
def transform_subscription_iterator(it: AsyncIterator[Any]) -> AsyncIterator[Any]:
    """
    Detect if the iterator is a MapAsyncIterator from graphql core which
    implements its own complicated close semantics and iterates via an
    intermediate task.  Replace it with a simpler solution using an
    async generator.
    """
    if hasattr(it, "_close_event"):
        try:
            return iterate_and_map(it.iterator, it.callback)  # type: ignore
        except AttributeError:  # pragma: no cover
            pass
    return it  # pragma: no cover


async def iterate_and_map(
    it: AsyncIterator[Any], map_func: Callable[[Any], Any]
) -> Any:
    """
    Iterate over an async iterator and map the values using the given function.
    In addition, it will close the iterator if it has an `aclose` method.
    """
    try:
        async for item in it:
            value = map_func(item)
            if isawaitable(value):
                value = await value
            yield value
    finally:
        if hasattr(it, "aclose"):
            await it.aclose()
