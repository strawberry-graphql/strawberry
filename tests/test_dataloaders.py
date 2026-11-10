import asyncio
import gc
import weakref
from asyncio.futures import Future
from collections.abc import Awaitable, Callable
from typing import Any, Optional, cast

import pytest
from pytest_mock import MockerFixture

from strawberry.dataloader import AbstractCache, DataLoader, DefaultCache
from strawberry.exceptions import WrongNumberOfResultsReturned

IDXType = Callable[[list[int]], Awaitable[list[int]]]


async def idx(keys: list[int]) -> list[int]:
    return keys


@pytest.mark.asyncio
async def test_loading():
    loader = DataLoader(load_fn=idx)

    value_a = await loader.load(1)
    value_b = await loader.load(2)
    value_c = await loader.load(3)

    assert value_a == 1
    assert value_b == 2
    assert value_c == 3

    values = await loader.load_many([1, 2, 3, 4, 5, 6])

    assert values == [1, 2, 3, 4, 5, 6]


@pytest.mark.asyncio
async def test_gathering(mocker: MockerFixture):
    mock_loader = mocker.Mock(side_effect=idx)

    loader = DataLoader(load_fn=cast("IDXType", mock_loader))

    [value_a, value_b, value_c] = await asyncio.gather(
        loader.load(1),
        loader.load(2),
        loader.load(3),
    )

    mock_loader.assert_called_once_with([1, 2, 3])

    assert value_a == 1
    assert value_b == 2
    assert value_c == 3


@pytest.mark.asyncio
@pytest.mark.parametrize("cache", [False, True])
async def test_max_batch_size(mocker: MockerFixture, cache: bool):
    mock_loader = mocker.Mock(side_effect=idx)

    loader = DataLoader(
        load_fn=cast("IDXType", mock_loader), max_batch_size=2, cache=cache
    )

    [value_a, value_b, value_c] = await asyncio.gather(
        loader.load(1),
        loader.load(2),
        loader.load(3),
    )

    mock_loader.assert_has_calls([mocker.call([1, 2]), mocker.call([3])])  # type: ignore

    assert value_a == 1
    assert value_b == 2
    assert value_c == 3


@pytest.mark.asyncio
async def test_error():
    async def idx(keys: list[int]) -> list[int | ValueError]:
        return [ValueError()]

    loader = DataLoader(load_fn=idx)

    with pytest.raises(ValueError):
        await loader.load(1)


@pytest.mark.asyncio
async def test_error_and_values():
    async def idx(keys: list[int]) -> list[int | ValueError]:
        return [2] if keys == [2] else [ValueError()]

    loader = DataLoader(load_fn=idx)

    with pytest.raises(ValueError):
        await loader.load(1)

    assert await loader.load(2) == 2


@pytest.mark.asyncio
async def test_when_raising_error_in_loader():
    async def idx(keys: list[int]) -> list[int | ValueError]:
        raise ValueError

    loader = DataLoader(load_fn=idx)

    with pytest.raises(ValueError):
        await loader.load(1)

    with pytest.raises(ValueError):
        await asyncio.gather(
            loader.load(1),
            loader.load(2),
            loader.load(3),
        )


@pytest.mark.asyncio
async def test_returning_wrong_number_of_results():
    async def idx(keys: list[int]) -> list[int]:
        return [1, 2]

    loader = DataLoader(load_fn=idx)

    with pytest.raises(
        WrongNumberOfResultsReturned,
        match=(
            "Received wrong number of results in dataloader, expected: 1, received: 2"
        ),
    ):
        await loader.load(1)


@pytest.mark.asyncio
async def test_caches_by_id(mocker: MockerFixture):
    mock_loader = mocker.Mock(side_effect=idx)

    loader = DataLoader(load_fn=cast("IDXType", mock_loader), cache=True)

    a = loader.load(1)
    b = loader.load(1)

    assert await a == 1
    assert await b == 1

    mock_loader.assert_called_once_with([1])


@pytest.mark.asyncio
async def test_caches_by_id_when_loading_many(mocker: MockerFixture):
    mock_loader = mocker.Mock(side_effect=idx)

    loader = DataLoader(load_fn=cast("IDXType", mock_loader), cache=True)

    a = loader.load(1)
    b = loader.load(1)

    assert await asyncio.gather(a, b) == [1, 1]

    mock_loader.assert_called_once_with([1])


@pytest.mark.asyncio
async def test_cache_disabled(mocker: MockerFixture):
    mock_loader = mocker.Mock(side_effect=idx)

    loader = DataLoader(load_fn=cast("IDXType", mock_loader), cache=False)

    a = loader.load(1)
    b = loader.load(1)

    assert a != b

    assert await a == 1
    assert await b == 1

    mock_loader.assert_has_calls([mocker.call([1, 1])])  # type: ignore


@pytest.mark.asyncio
async def test_cache_disabled_immediate_await(mocker: MockerFixture):
    mock_loader = mocker.Mock(side_effect=idx)

    loader = DataLoader(load_fn=cast("IDXType", mock_loader), cache=False)

    a = await loader.load(1)
    b = await loader.load(1)

    assert a == b

    mock_loader.assert_has_calls([mocker.call([1]), mocker.call([1])])  # type: ignore


@pytest.mark.asyncio
async def test_prime():
    async def idx(keys: list[int | float]) -> list[int | float]:
        assert keys, "At least one key must be specified"
        return keys

    loader = DataLoader(load_fn=idx)

    # Basic behavior intact
    a1 = loader.load(1)
    assert await a1 == 1

    # Prime doesn't overrides value
    loader.prime(1, 1.1)
    loader.prime(2, 2.1)
    b1 = loader.load(1)
    b2 = loader.load(2)
    assert await b1 == 1
    assert await b2 == 2.1

    # Unless you tell it to
    loader.prime(1, 1.2, force=True)
    loader.prime(2, 2.2, force=True)
    b1 = loader.load(1)
    b2 = loader.load(2)
    assert await b1 == 1.2
    assert await b2 == 2.2

    # Preset will override pending values, but not cached values
    c2 = loader.load(2)  # This is in cache
    c3 = loader.load(3)  # This is pending
    loader.prime_many({2: 2.3, 3: 3.3}, force=True)
    assert await c2 == 2.2
    assert await c3 == 3.3

    # If we prime all keys in a batch, the load_fn is never called
    # (See assertion in idx)
    c4 = loader.load(4)
    loader.prime_many({4: 4.4})
    assert await c4 == 4.4

    # Yield to ensure the last batch has been dispatched,
    # despite all values being primed
    await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_prime_nocache():
    async def idx(keys: list[int | float]) -> list[int | float]:
        assert keys, "At least one key must be specified"
        return keys

    loader = DataLoader(load_fn=idx, cache=False)

    # Primed value is ignored
    loader.prime(1, 1.1)
    a1 = loader.load(1)
    assert await a1 == 1

    # Unless it affects pending value in the current batch
    b1 = loader.load(2)
    loader.prime(2, 2.2)
    assert await b1 == 2.2

    # Yield to ensure the last batch has been dispatched,
    # despite all values being primed
    await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_clear():
    batch_num = 0

    async def idx(keys: list[int]) -> list[tuple[int, int]]:
        """Maps key => (key, batch_num)"""
        nonlocal batch_num
        batch_num += 1
        return [(key, batch_num) for key in keys]

    loader = DataLoader(load_fn=idx)

    assert await loader.load_many([1, 2, 3]) == [(1, 1), (2, 1), (3, 1)]

    loader.clear(1)

    assert await loader.load_many([1, 2, 3]) == [(1, 2), (2, 1), (3, 1)]

    loader.clear_many([1, 2])

    assert await loader.load_many([1, 2, 3]) == [(1, 3), (2, 3), (3, 1)]

    loader.clear_all()

    assert await loader.load_many([1, 2, 3]) == [(1, 4), (2, 4), (3, 4)]


@pytest.mark.asyncio
async def test_clear_nocache():
    batch_num = 0

    async def idx(keys: list[int]) -> list[tuple[int, int]]:
        """Maps key => (key, batch_num)"""
        nonlocal batch_num
        batch_num += 1
        return [(key, batch_num) for key in keys]

    loader = DataLoader(load_fn=idx, cache=False)

    assert await loader.load_many([1, 2, 3]) == [(1, 1), (2, 1), (3, 1)]

    loader.clear(1)

    assert await loader.load_many([1, 2, 3]) == [(1, 2), (2, 2), (3, 2)]

    loader.clear_many([1, 2])

    assert await loader.load_many([1, 2, 3]) == [(1, 3), (2, 3), (3, 3)]

    loader.clear_all()

    assert await loader.load_many([1, 2, 3]) == [(1, 4), (2, 4), (3, 4)]


@pytest.mark.asyncio
async def test_dont_dispatch_cancelled():
    async def idx(keys: list[int]) -> list[int]:
        await asyncio.sleep(0.2)
        return keys

    loader = DataLoader(load_fn=idx)

    value_a = await loader.load(1)
    # value_b will be cancelled by hand
    value_b = cast("Future[Any]", loader.load(2))
    value_b.cancel()
    # value_c will be cancelled by the timeout
    value_c = cast("Future[Any]", loader.load(3))
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(value_c, 0.1)
    value_d = await loader.load(4)

    assert value_a == 1
    assert value_d == 4

    # 2 can still be used here because a new future will be created for it
    values = await loader.load_many([1, 2, 3, 4, 5, 6])
    assert values == [1, 2, 3, 4, 5, 6]

    with pytest.raises(asyncio.CancelledError):
        value_b.result()
    with pytest.raises(asyncio.CancelledError):
        value_c.result()  # pyright: ignore

    # Try single loading results again to make sure the cancelled
    # futures are not being reused
    value_a = await loader.load(1)
    value_b = await loader.load(2)
    value_c = await loader.load(3)
    value_d = await loader.load(4)

    assert value_a == 1
    assert value_b == 2
    assert value_c == 3
    assert value_d == 4


@pytest.mark.asyncio
async def test_cancelled_future_with_failing_loader():
    """When the load function raises and some futures are already cancelled,
    the error handler should skip cancelled futures instead of raising
    InvalidStateError.

    This reproduces a real-world scenario where a client disconnects
    mid-request: some DataLoader futures get cancelled by the event loop,
    then the batch load function fails (e.g. because the executor is torn
    down). The error handler must not crash trying to set_exception on
    the already-cancelled futures.
    """

    async def failing_loader(keys: list[int]) -> list[int]:
        raise RuntimeError("executor is broken")

    loader = DataLoader(load_fn=failing_loader, cache=False)

    future_a = cast("Future[Any]", loader.load(1))
    future_b = cast("Future[Any]", loader.load(2))
    future_c = cast("Future[Any]", loader.load(3))

    # Simulate a client disconnect cancelling one of the futures before
    # the batch dispatches
    future_a.cancel()

    # Let the event loop dispatch the batch — this must not raise
    # InvalidStateError from trying to set_exception on the cancelled future.
    # Two yields: one for call_soon to fire create_task, one for the task to run.
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    # The cancelled future should remain cleanly cancelled — not broken by
    # an InvalidStateError inside dispatch_batch
    assert future_a.cancelled()
    with pytest.raises(asyncio.CancelledError):
        future_a.result()

    # The non-cancelled futures should have received the loader's exception
    # (without the fix, dispatch_batch crashes on future_a before reaching these)
    with pytest.raises(RuntimeError, match="executor is broken"):
        future_b.result()
    with pytest.raises(RuntimeError, match="executor is broken"):
        future_c.result()


@pytest.mark.asyncio
@pytest.mark.parametrize("cache", [False, True])
async def test_all_futures_cancelled_skips_load_fn(cache: bool):
    """When all futures in a batch are cancelled before dispatch, the load_fn
    should not be called at all.  This prevents wasted work like database
    queries whose results no one is waiting for.
    """
    call_count = 0

    async def counting_loader(keys: list[int]) -> list[int]:
        nonlocal call_count
        call_count += 1
        return keys

    loader = DataLoader(load_fn=counting_loader, cache=cache)

    future_a = cast("Future[Any]", loader.load(1))
    future_b = cast("Future[Any]", loader.load(2))

    # Cancel all futures before the batch dispatches
    future_a.cancel()
    future_b.cancel()

    # Let the event loop dispatch (call_soon → create_task → dispatch_batch)
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    assert future_a.cancelled()
    assert future_b.cancelled()
    assert call_count == 0, "load_fn should not have been called"


@pytest.mark.asyncio
@pytest.mark.parametrize("cache", [False, True])
async def test_cancelled_futures_cancel_dispatch_task(cache: bool):
    """When all futures in a batch are cancelled, the underlying dispatch
    task should also be cancelled.  This is important for resource cleanup
    when using asyncio.TaskGroup or similar structured concurrency patterns.
    """

    async def slow_loader(keys: list[int]) -> list[int]:
        await asyncio.sleep(10)
        return keys

    loader = DataLoader(load_fn=slow_loader, cache=cache)

    future_a = cast("Future[Any]", loader.load(1))
    future_b = cast("Future[Any]", loader.load(2))

    # Let call_soon fire so the dispatch task is created
    await asyncio.sleep(0)
    # Let the task start and suspend inside slow_loader's asyncio.sleep(10)
    await asyncio.sleep(0)

    assert loader.batch is not None
    dispatch_task = loader.batch._dispatch_task
    assert dispatch_task is not None
    assert not dispatch_task.done()

    # Cancel all futures — this should cascade to the dispatch task
    future_a.cancel()
    future_b.cancel()

    # Give the event loop a chance to run _on_future_done callbacks
    # and propagate CancelledError to the dispatch task
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    assert dispatch_task.cancelled()


@pytest.mark.asyncio
@pytest.mark.parametrize("cache", [False, True])
async def test_cancelled_futures_cancel_running_dispatch(cache: bool):
    """When all futures are cancelled after load_fn has already started,
    the dispatch task should still be cancelled, interrupting the in-progress
    load_fn via CancelledError.
    """
    load_started = asyncio.Event()

    async def slow_loader(keys: list[int]) -> list[int]:
        load_started.set()
        # Block until cancelled
        await asyncio.sleep(10)
        return keys

    loader = DataLoader(load_fn=slow_loader, cache=cache)

    future_a = cast("Future[Any]", loader.load(1))
    future_b = cast("Future[Any]", loader.load(2))

    # Let call_soon fire and dispatch_batch start running
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    await load_started.wait()

    assert loader.batch is not None
    dispatch_task = loader.batch._dispatch_task
    assert dispatch_task is not None
    assert not dispatch_task.done()

    # Cancel all futures while load_fn is in progress
    future_a.cancel()
    future_b.cancel()

    # Give the event loop a chance to propagate cancellation
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    assert future_a.cancelled()
    assert future_b.cancelled()
    assert dispatch_task.done()


@pytest.mark.asyncio
@pytest.mark.parametrize("cache", [False, True])
async def test_partial_cancellation_still_dispatches(cache: bool):
    """When only some futures in a batch are cancelled, the batch should
    still dispatch and deliver results for the non-cancelled futures.
    """
    call_count = 0

    async def counting_loader(keys: list[int]) -> list[int]:
        nonlocal call_count
        call_count += 1
        return keys

    loader = DataLoader(load_fn=counting_loader, cache=cache)

    future_a = cast("Future[Any]", loader.load(1))
    future_b = cast("Future[Any]", loader.load(2))
    future_c = cast("Future[Any]", loader.load(3))

    # Cancel only one future
    future_b.cancel()

    # Let the batch dispatch
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    assert future_a.result() == 1
    assert future_b.cancelled()
    assert future_c.result() == 3
    assert call_count == 1, "load_fn should still be called for non-cancelled futures"


@pytest.mark.asyncio
async def test_cache_override():
    class TestCache(AbstractCache[int, int]):
        def __init__(self):
            self.cache: dict[int, Future[int]] = {}

        def get(self, key: int) -> Optional["Future[int]"]:
            return self.cache.get(key)

        def set(self, key: int, value: "Future[int]") -> None:
            self.cache[key] = value

        def delete(self, key: int) -> None:
            del self.cache[key]

        def clear(self) -> None:
            self.cache.clear()

    custom_cache = TestCache()
    loader = DataLoader(load_fn=idx, cache_map=custom_cache)

    await loader.load(1)
    await loader.load(2)
    await loader.load(3)

    assert len(custom_cache.cache) == 3
    assert await custom_cache.cache[1] == 1
    assert await custom_cache.cache[2] == 2
    assert await custom_cache.cache[3] == 3

    loader.clear(1)
    assert len(custom_cache.cache) == 2
    assert sorted(custom_cache.cache.keys()) == [2, 3]

    loader.clear_all()
    assert len(custom_cache.cache) == 0
    assert not list(custom_cache.cache.keys())

    await loader.load(1)
    await loader.load(2)
    await loader.load(3)

    loader.clear_many([1, 2])
    assert len(custom_cache.cache) == 1
    assert list(custom_cache.cache.keys()) == [3]

    data = await loader.load(3)
    assert data == 3

    loader.prime(3, 4)
    assert await custom_cache.cache[3] == 3

    loader.prime(3, 4, True)
    assert await custom_cache.cache[3] == 4

    with pytest.raises(TypeError, match="unhashable type: 'list'"):
        await loader.load([1, 2, 3])  # type: ignore

    data = await loader.load((1, 2, 3))  # type: ignore
    assert await custom_cache.get((1, 2, 3)) == data  # type: ignore


@pytest.mark.asyncio
async def test_custom_cache_key_fn():
    def custom_cache_key(key: list[int]) -> str:
        return ",".join(str(k) for k in key)

    loader = DataLoader(load_fn=idx, cache_key_fn=custom_cache_key)
    data = await loader.load([1, 2, "test"])
    assert data == [1, 2, "test"]


@pytest.mark.asyncio
async def test_user_class_custom_cache_key_fn():
    class CustomData:
        def __init__(self, custom_id: int, name: str):
            self.id: int = custom_id
            self.name: str = name

    def custom_cache_key(key: CustomData) -> int:
        return key.id

    loader = DataLoader(load_fn=idx, cache_key_fn=custom_cache_key)
    data1 = await loader.load(CustomData(1, "Nick"))
    data2 = await loader.load(CustomData(1, "Nick"))
    assert data1 == data2

    data2 = await loader.load(CustomData(2, "Jane"))
    assert data1 != data2


def test_works_when_created_in_a_different_loop(mocker: MockerFixture):
    mock_loader = mocker.Mock(side_effect=idx)
    loader = DataLoader(load_fn=cast("IDXType", mock_loader), cache=False)

    loop = asyncio.new_event_loop()

    async def run():
        return await loader.load(1)

    data = loop.run_until_complete(run())

    assert data == 1

    mock_loader.assert_called_once_with([1])


@pytest.mark.asyncio
@pytest.mark.parametrize("cache", [False, True])
async def test_batching_window(cache: bool):
    calls: list[list[int]] = []

    async def load(keys: list[int]) -> list[int]:
        calls.append(keys)
        return keys

    loader = DataLoader(load_fn=load, cache=cache)
    first = loader.load(1)
    # Scheduling the dispatch task must still allow loads in this next turn
    # to join the batch, before load_fn starts.
    await asyncio.sleep(0)
    second = loader.load(2)
    assert calls == []
    assert await asyncio.gather(first, second) == [1, 2]
    assert await loader.load(3) == 3
    assert calls == [[1, 2], [3]]


@pytest.mark.asyncio
@pytest.mark.parametrize("cache", [False, True])
async def test_prime_empty_batch_then_load(cache: bool):
    calls: list[list[int]] = []

    async def load(keys: list[int]) -> list[int]:
        calls.append(keys)
        return keys

    loader = DataLoader(load_fn=load, cache=cache, max_batch_size=2)
    first = loader.load(1)
    loader.prime(1, 10)
    # A pending dispatch for the emptied batch must not affect later loads.
    assert await loader.load_many([2, 3, 4]) == [2, 3, 4]
    assert await first == 10
    assert calls == [[2, 3], [4]]


@pytest.mark.asyncio
@pytest.mark.parametrize("cache", [False, True])
async def test_partial_cancellation_during_load(cache: bool):
    started = asyncio.Event()
    finish = asyncio.Event()
    calls: list[list[int]] = []

    async def load(keys: list[int]) -> list[int]:
        calls.append(keys)
        started.set()
        await finish.wait()
        return keys

    loader = DataLoader(load_fn=load, cache=cache)
    first = cast("Future[int]", loader.load(1))
    second = loader.load(2)
    await started.wait()
    first.cancel()
    await asyncio.sleep(0)
    finish.set()

    assert await asyncio.wait_for(second, timeout=1) == 2
    assert first.cancelled()
    # A cancelled cached future must be replaced on the next load.
    assert await asyncio.wait_for(loader.load(1), timeout=1) == 1
    assert calls == [[1, 2], [1]]


@pytest.mark.asyncio
async def test_cancelling_one_caller_of_a_cached_key_does_not_cancel_others():
    """Callers that load the same cached key share one pending load, but
    cancelling one of them must not cancel the others.
    """
    calls: list[list[int]] = []

    async def load(keys: list[int]) -> list[int]:
        calls.append(keys)
        await asyncio.sleep(0)
        return keys

    loader = DataLoader(load_fn=load)
    first = asyncio.ensure_future(loader.load(1))
    second = asyncio.ensure_future(loader.load(1))
    await asyncio.sleep(0)
    first.cancel()

    assert await asyncio.wait_for(second, timeout=1) == 1
    assert first.cancelled()
    assert calls == [[1]]


@pytest.mark.asyncio
async def test_cancelling_one_caller_while_loading_does_not_cancel_others():
    started = asyncio.Event()
    finish = asyncio.Event()
    calls: list[list[int]] = []

    async def load(keys: list[int]) -> list[int]:
        calls.append(keys)
        started.set()
        await finish.wait()
        return keys

    loader = DataLoader(load_fn=load)
    first = cast("Future[int]", loader.load(1))
    second = loader.load(1)
    await started.wait()
    first.cancel()
    await asyncio.sleep(0)
    # A caller arriving after the cancellation joins the pending load.
    third = loader.load(1)
    finish.set()

    assert await asyncio.wait_for(asyncio.gather(second, third), timeout=1) == [1, 1]
    assert first.cancelled()
    assert calls == [[1]]
    # The cached value is still served to later callers.
    assert await loader.load(1) == 1
    assert calls == [[1]]


@pytest.mark.asyncio
async def test_cancelling_one_load_many_does_not_cancel_other_callers():
    calls: list[list[int]] = []

    async def load(keys: list[int]) -> list[int]:
        calls.append(keys)
        await asyncio.sleep(0)
        return keys

    loader = DataLoader(load_fn=load)
    first = cast("Future[list[int]]", loader.load_many([1, 2]))
    second = loader.load_many([2, 3])
    await asyncio.sleep(0)
    first.cancel()

    assert await asyncio.wait_for(second, timeout=1) == [2, 3]
    assert calls == [[1, 2, 3]]


@pytest.mark.asyncio
async def test_error_is_delivered_to_every_caller_of_a_cached_key():
    async def load(keys: list[int]) -> list[int | BaseException]:
        return [ValueError(f"error {key}") for key in keys]

    loader = DataLoader(load_fn=load)
    results = await asyncio.gather(
        loader.load(1), loader.load(1), return_exceptions=True
    )

    assert [str(result) for result in results] == ["error 1", "error 1"]


@pytest.mark.asyncio
async def test_all_callers_of_a_cached_key_cancelled_skips_load_fn():
    """load_fn is still skipped when every caller of a shared key is cancelled."""
    calls: list[list[int]] = []

    async def load(keys: list[int]) -> list[int]:
        calls.append(keys)
        return keys

    loader = DataLoader(load_fn=load)
    first = cast("Future[int]", loader.load(1))
    second = cast("Future[int]", loader.load(1))
    first.cancel()
    second.cancel()

    await asyncio.sleep(0)
    await asyncio.sleep(0)

    assert first.cancelled()
    assert second.cancelled()
    assert calls == []
    # The abandoned load is not served from the cache.
    assert await loader.load(1) == 1
    assert calls == [[1]]


@pytest.mark.asyncio
async def test_all_callers_of_a_cached_key_cancelled_cancels_running_dispatch():
    started = asyncio.Event()

    async def load(keys: list[int]) -> list[int]:
        started.set()
        await asyncio.sleep(10)
        return keys

    loader = DataLoader(load_fn=load)
    first = cast("Future[int]", loader.load(1))
    second = cast("Future[int]", loader.load(1))
    await started.wait()

    assert loader.batch is not None
    dispatch_task = loader.batch._dispatch_task
    assert dispatch_task is not None

    first.cancel()
    second.cancel()
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    assert dispatch_task.cancelled()


@pytest.mark.asyncio
async def test_all_callers_of_one_cached_key_cancelled_still_loads_other_keys():
    calls: list[list[int]] = []

    async def load(keys: list[int]) -> list[int]:
        calls.append(keys)
        await asyncio.sleep(0)
        return keys

    loader = DataLoader(load_fn=load)
    first = cast("Future[int]", loader.load(1))
    second = cast("Future[int]", loader.load(1))
    other = loader.load(2)
    first.cancel()
    second.cancel()

    assert await asyncio.wait_for(other, timeout=1) == 2
    # As for uncached keys, the batch keeps the keys whose callers were cancelled
    assert calls == [[1, 2]]


@pytest.mark.asyncio
@pytest.mark.parametrize("cache", [False, True])
async def test_load_after_batch_cancelled_before_dispatch(cache: bool):
    """A batch whose dispatch was cancelled must not swallow later loads."""
    calls: list[list[int]] = []

    async def load(keys: list[int]) -> list[int]:
        calls.append(keys)
        return keys

    loader = DataLoader(load_fn=load, cache=cache)
    first = cast("Future[int]", loader.load(1))
    second = cast("Future[int]", loader.load(2))
    first.cancel()
    second.cancel()
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    assert await asyncio.wait_for(loader.load(3), timeout=1) == 3
    assert calls == [[3]]


@pytest.mark.asyncio
async def test_load_while_a_batch_is_skipped_at_dispatch_starts_a_new_batch():
    """A load joining a batch that is then skipped must not wait for it forever.

    Here the cancellation of the only caller hasn't reached the shared future
    when the dispatch skips the batch, and a new load of the same key comes in
    right after.
    """
    calls: list[list[int]] = []

    async def load(keys: list[int]) -> list[int]:
        calls.append(keys)
        return keys

    loader = DataLoader(load_fn=load)
    first = cast("Future[int]", loader.load(1))
    # Let the dispatch task be created.
    await asyncio.sleep(0)

    later_loads: list[Awaitable[int]] = []
    asyncio.get_running_loop().call_soon(lambda: later_loads.append(loader.load(1)))
    first.cancel()
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    assert await asyncio.wait_for(later_loads[0], timeout=1) == 1
    assert calls == [[1]]


@pytest.mark.asyncio
@pytest.mark.parametrize("cache", [False, True])
async def test_load_errors_are_not_reported_as_never_retrieved(cache: bool):
    reported: list[dict[str, Any]] = []
    loop = asyncio.get_running_loop()
    loop.set_exception_handler(lambda _, context: reported.append(context))

    async def load(keys: list[int]) -> list[int | BaseException]:
        return [ValueError(f"error {key}") for key in keys]

    try:
        loader = DataLoader(load_fn=load, cache=cache)
        results = await asyncio.gather(
            loader.load(1), loader.load(1), loader.load(2), return_exceptions=True
        )
        assert [str(result) for result in results] == [
            "error 1",
            "error 1",
            "error 2",
        ]

        loader.clear_all()
        del loader
        del results
        gc.collect()

        assert reported == []
    finally:
        loop.set_exception_handler(None)


@pytest.mark.asyncio
async def test_prime_after_a_cancellation_still_dispatches_other_keys():
    """Priming removes the cancelled key from the batch, before its callback runs."""
    calls: list[list[int]] = []

    async def load(keys: list[int]) -> list[int]:
        calls.append(keys)
        return keys

    loader = DataLoader(load_fn=load, cache=False)
    cancelled = cast("Future[int]", loader.load(1))
    primed = loader.load(2)
    other = loader.load(3)
    cancelled.cancel()
    loader.prime(2, 20)

    assert await asyncio.wait_for(primed, timeout=1) == 20
    assert await asyncio.wait_for(other, timeout=1) == 3
    assert calls == [[3]]


@pytest.mark.asyncio
async def test_cancelling_the_cached_future_cancels_every_caller():
    loader = DataLoader(load_fn=idx)
    first = loader.load(1)
    second = loader.load(1)

    cached = loader.cache_map.get(1)
    assert cached is not None
    cached.cancel()

    results = await asyncio.gather(first, second, return_exceptions=True)
    assert all(isinstance(result, asyncio.CancelledError) for result in results)


@pytest.mark.asyncio
@pytest.mark.parametrize("cache", [False, True])
async def test_all_callers_cancelled_after_dispatch_is_scheduled_skips_load_fn(
    cache: bool,
):
    """Callers cancelled once the dispatch task exists, but before it runs.

    The cancellation of a cached key's callers only reaches the shared
    future in a later loop iteration, load_fn must be skipped regardless.
    """
    calls: list[list[int]] = []

    async def load(keys: list[int]) -> list[int]:
        calls.append(keys)
        return keys

    async def resolver(key: int) -> int:
        return await loader.load(key)

    loader = DataLoader(load_fn=load, cache=cache)
    callers = [asyncio.ensure_future(resolver(key)) for key in [1, 1, 2]]
    # Let the resolvers call load, and the dispatch task be created.
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    for caller in callers:
        caller.cancel()

    await asyncio.sleep(0)
    await asyncio.sleep(0)

    assert all(caller.cancelled() for caller in callers)
    assert calls == []
    assert await asyncio.wait_for(loader.load(1), timeout=1) == 1
    assert calls == [[1]]


@pytest.mark.asyncio
async def test_loading_a_key_again_right_after_cancelling_its_caller():
    calls: list[list[int]] = []

    async def load(keys: list[int]) -> list[int]:
        calls.append(keys)
        return keys

    loader = DataLoader(load_fn=load)
    first = cast("Future[int]", loader.load(1))
    first.cancel()
    # The cancellation isn't processed yet, the new caller joins the load.
    second = loader.load(1)

    assert await asyncio.wait_for(second, timeout=1) == 1
    assert first.cancelled()
    assert calls == [[1]]


@pytest.mark.asyncio
async def test_prime_resolves_every_caller_of_a_pending_key():
    calls: list[list[int]] = []

    async def load(keys: list[int]) -> list[int]:
        calls.append(keys)
        return keys

    loader = DataLoader(load_fn=load)
    first = loader.load(1)
    second = loader.load(1)
    loader.prime(1, 10)

    assert await asyncio.gather(first, second) == [10, 10]
    assert calls == []


@pytest.mark.asyncio
async def test_cache_returning_a_future_not_created_by_the_loader():
    future: Future[int] = asyncio.get_running_loop().create_future()

    class StaticCache(AbstractCache[int, int]):
        def get(self, key: int) -> Future[int] | None:
            return future

        def set(self, key: int, value: Future[int]) -> None:
            pass

        def delete(self, key: int) -> None:
            pass

        def clear(self) -> None:
            pass

    loader = DataLoader(load_fn=idx, cache_map=StaticCache())
    loaded = loader.load(1)
    future.set_result(42)

    assert await asyncio.wait_for(loaded, timeout=1) == 42


@pytest.mark.asyncio
async def test_cancelling_a_caller_of_a_future_not_created_by_the_loader():
    future: Future[int] = asyncio.get_running_loop().create_future()

    class StaticCache(AbstractCache[int, int]):
        def get(self, key: int) -> Future[int] | None:
            return future

        def set(self, key: int, value: Future[int]) -> None:
            pass

        def delete(self, key: int) -> None:
            pass

        def clear(self) -> None:
            pass

    loader = DataLoader(load_fn=idx, cache_map=StaticCache())
    first = cast("Future[int]", loader.load(1))
    second = loader.load(1)
    first.cancel()
    await asyncio.sleep(0)
    future.set_result(42)

    assert await asyncio.wait_for(second, timeout=1) == 42
    assert first.cancelled()


@pytest.mark.asyncio
async def test_failing_cache_write_does_not_load_the_key():
    calls: list[list[int]] = []

    async def load(keys: list[int]) -> list[int]:
        calls.append(keys)
        return keys

    class FailingCache(DefaultCache[int, int]):
        def set(self, key: int, value: Future[int]) -> None:
            if key == 1:
                raise RuntimeError("Cache unavailable")
            super().set(key, value)

    loader = DataLoader(load_fn=load, cache_map=FailingCache())
    with pytest.raises(RuntimeError, match="Cache unavailable"):
        loader.load(1)

    assert await loader.load(2) == 2
    assert calls == [[2]]


@pytest.mark.asyncio
async def test_cancelling_a_caller_of_a_cache_shared_between_loaders():
    calls: list[list[int]] = []

    async def load(keys: list[int]) -> list[int]:
        calls.append(keys)
        await asyncio.sleep(0)
        return keys

    cache_map: AbstractCache[int, int] = DataLoader(load_fn=load).cache_map
    first_loader = DataLoader(load_fn=load, cache_map=cache_map)
    second_loader = DataLoader(load_fn=load, cache_map=cache_map)

    first = cast("Future[int]", first_loader.load(1))
    second = second_loader.load(1)
    first.cancel()

    assert await asyncio.wait_for(second, timeout=1) == 1
    assert calls == [[1]]


@pytest.mark.asyncio
@pytest.mark.parametrize("cache", [False, True])
async def test_loaded_values_are_freed_without_garbage_collection(cache: bool):
    """The loader must not create reference cycles keeping loaded values alive."""

    class Value:
        pass

    refs: list[weakref.ref[Value]] = []

    async def load(keys: list[int]) -> list[Value]:
        values = [Value() for _ in keys]
        refs.extend(weakref.ref(value) for value in values)
        return values

    gc.disable()
    try:
        loader = DataLoader(load_fn=load, cache=cache)
        await loader.load_many([1, 2, 3])
        # Start a new batch, so that the loader no longer refers to the first.
        await loader.load(4)
        loader.clear_all()
        del loader
        await asyncio.sleep(0)

        assert [ref() for ref in refs] == [None] * 4
    finally:
        gc.enable()
