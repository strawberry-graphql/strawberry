import asyncio
import types
from collections.abc import Generator
from typing import Any

import pytest
from graphql.pyutils import is_awaitable

from strawberry.execution import optimized_is_awaitable


class CustomAwaitable:
    def __await__(self) -> Generator[None, None, int]:
        yield
        return 1


class AwaitableInt(int, CustomAwaitable):
    pass


class AsyncIterable:
    def __aiter__(self) -> Any:
        return self

    async def __anext__(self) -> int:
        raise StopAsyncIteration


@types.coroutine
def generator_coroutine() -> Generator[None, None, int]:
    yield
    return 1


async def native_coroutine() -> int:
    return 1


@pytest.mark.parametrize(
    "value",
    [
        None,
        False,
        1,
        1.2,
        "x",
        b"x",
        bytearray(),
        [],
        (),
        {},
        set(),
        frozenset(),
        object(),
        CustomAwaitable(),
        AwaitableInt(1),
        AsyncIterable(),
    ],
)
def test_values(value: Any) -> None:
    assert optimized_is_awaitable(value) is is_awaitable(value)


@pytest.mark.parametrize(
    "factory", [native_coroutine, generator_coroutine, lambda: (x for x in [])]
)
def test_coroutines_and_generators(factory: Any) -> None:
    value = factory()
    try:
        assert optimized_is_awaitable(value) is is_awaitable(value)
    finally:
        value.close()


@pytest.mark.asyncio
async def test_future_and_task() -> None:
    future = asyncio.get_running_loop().create_future()
    task = asyncio.create_task(native_coroutine())
    try:
        for value in (future, task):
            assert optimized_is_awaitable(value) is is_awaitable(value) is True
        future.set_result(1)
        assert await future == await task == 1
        for value in (future, task):
            assert optimized_is_awaitable(value) is True
    finally:
        if not task.done():
            task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        future.cancel()


@pytest.mark.parametrize("attribute", ["__class__", "__await__"])
@pytest.mark.parametrize("error", [None, AttributeError, RuntimeError])
@pytest.mark.parametrize("spoof", [None, types.CoroutineType, types.GeneratorType])
def test_attribute_order_and_exceptions(attribute: str, error: Any, spoof: Any) -> None:
    class Unusual:
        def __getattribute__(self, name: str) -> Any:
            events.append(name)
            if name == attribute and error:
                raise error("descriptor failed")
            if name == "__class__" and spoof:
                return spoof
            if name == "__await__":
                return None  # graphql-core checks presence, not callability
            return object.__getattribute__(self, name)

    def observe(detector: Any) -> tuple[Any, list[str]]:
        events.clear()
        try:
            result = detector(Unusual())
        except (AttributeError, RuntimeError) as exc:
            result = (type(exc), str(exc))
        return result, events.copy()

    events: list[str] = []
    assert observe(optimized_is_awaitable) == observe(is_awaitable)


@pytest.mark.parametrize("error", [None, AttributeError, RuntimeError])
def test_await_descriptor(error: Any) -> None:
    events: list[str] = []

    class Descriptor:
        @property
        def __await__(self) -> Any:
            events.append("await")
            if error:
                raise error("failed")
            return None

    if error is RuntimeError:
        with pytest.raises(RuntimeError, match="failed"):
            optimized_is_awaitable(Descriptor())
    else:
        assert optimized_is_awaitable(Descriptor()) is (error is None)
    assert events == ["await"]


def test_orm_like_dynamic_attributes() -> None:
    accesses: list[str] = []

    class Model:
        def __getattr__(self, name: str) -> Any:
            accesses.append(name)
            raise AttributeError(name)

    assert optimized_is_awaitable(Model()) is False
    assert accesses == ["__await__"]


@pytest.mark.parametrize(
    "base", [int, float, str, bytes, bytearray, list, tuple, dict, set, frozenset]
)
def test_primitive_subclasses(base: type) -> None:
    subclass = type(
        "AwaitablePrimitive", (base,), {"__await__": CustomAwaitable.__await__}
    )
    value = subclass()
    assert optimized_is_awaitable(value) is is_awaitable(value) is True
