from __future__ import annotations

import asyncio
import dataclasses
from abc import ABC, abstractmethod
from asyncio import create_task, gather, get_event_loop
from asyncio.futures import Future
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    TypeVar,
    overload,
)

from .exceptions import WrongNumberOfResultsReturned

if TYPE_CHECKING:
    from asyncio.events import AbstractEventLoop
    from collections.abc import (
        Awaitable,
        Callable,
        Hashable,
        Iterable,
        Mapping,
        Sequence,
    )


T = TypeVar("T")
K = TypeVar("K")


@dataclass(slots=True)
class LoaderTask(Generic[K, T]):
    key: K
    future: Future
    # Only used for cached keys. Every `load` of a cached key gets its own
    # waiter future, so that cancelling one caller doesn't cancel the others
    # waiting for the same key. `future` is cancelled once all waiters are.
    waiters: list[Future] | None = dataclasses.field(default=None, repr=False)
    _live_waiters: int = dataclasses.field(default=0, repr=False)
    _batch: Batch[K, T] | None = dataclasses.field(default=None, repr=False)
    _cancellation_handled: bool = dataclasses.field(default=False, repr=False)

    def add_waiter(self, loop: AbstractEventLoop) -> Future:
        waiter = loop.create_future()
        if self.waiters is None:
            self.waiters = [waiter]
        else:
            self.waiters.append(waiter)
        self._live_waiters += 1
        waiter.add_done_callback(self._on_waiter_done)
        return waiter

    def set_result(self, value: Any) -> None:
        self.future.set_result(value)
        if self.waiters:
            for waiter in self.waiters:
                if not waiter.done():
                    # Resolved here, so the callback has nothing to do.
                    waiter.remove_done_callback(self._on_waiter_done)
                    waiter.set_result(value)

    def set_exception(self, exception: BaseException) -> None:
        self.future.set_exception(exception)
        if self.waiters:
            # Callers get the exception from their waiters, mark it as
            # retrieved on the shared future so asyncio doesn't log it.
            self.future.exception()
            for waiter in self.waiters:
                if not waiter.done():
                    waiter.remove_done_callback(self._on_waiter_done)
                    waiter.set_exception(exception)

    @property
    def _is_abandoned(self) -> bool:
        """Whether no caller is waiting for the task's result anymore.

        Waiters are checked directly, as their cancellation only reaches
        `future` once their callbacks run, in a later loop iteration.
        """
        if self.future.cancelled():
            return True
        return self.waiters is not None and all(w.cancelled() for w in self.waiters)

    def _on_waiter_done(self, waiter: Future) -> None:
        if not waiter.cancelled():
            return

        self._live_waiters -= 1
        if self._live_waiters == 0 and not self.future.done():
            self.future.cancel()
            # Don't wait for the future's callback to cancel the dispatch.
            self._handle_cancellation()

    def _on_future_done(self, future: Future) -> None:
        if isinstance(future, _CachedFuture):
            self._resolve_pending_waiters()
            # The cache only needs the resolved future.
            future.task = None

        if future.cancelled():
            self._handle_cancellation()

        # Release the batch and the waiters, so that they are freed by
        # refcounting.
        self._batch = None
        self.waiters = None

    def _handle_cancellation(self) -> None:
        if self._cancellation_handled:
            return
        self._cancellation_handled = True
        if self._batch is not None:
            self._batch._on_task_cancelled()

    def _resolve_pending_waiters(self) -> None:
        """Resolve the waiters left pending by a future resolved elsewhere.

        For example, when the future is cancelled through the cache.
        """
        if not self.waiters:
            return

        for waiter in self.waiters:
            if waiter.done():
                continue
            if self.future.cancelled():
                waiter.cancel()
            elif (exception := self.future.exception()) is not None:
                waiter.set_exception(exception)
            else:
                waiter.set_result(self.future.result())


class _CachedFuture(Future[T]):
    """The future stored in the cache, linked to its task until it is done."""

    __slots__ = ("task",)

    task: LoaderTask[Any, T] | None


@dataclass(slots=True)
class Batch(Generic[K, T]):
    tasks: list[LoaderTask] = dataclasses.field(default_factory=list)
    dispatched: bool = False
    _dispatch_task: asyncio.Task[None] | None = dataclasses.field(
        default=None, repr=False
    )
    _abandoned: bool = dataclasses.field(default=False, repr=False)
    # Number of tasks whose future isn't cancelled
    _live_tasks: int = dataclasses.field(default=0, repr=False)

    def add_task(self, key: Any, future: Future) -> LoaderTask[K, T]:
        task: LoaderTask[K, T] = LoaderTask(key, future, _batch=self)
        self.tasks.append(task)
        self._live_tasks += 1
        future.add_done_callback(task._on_future_done)
        return task

    def _remove_done_tasks(self) -> None:
        tasks = []
        for task in self.tasks:
            if task.future.done():
                # Its pending callback must not update this batch anymore
                task._batch = None
            else:
                tasks.append(task)
        self.tasks = tasks
        self._live_tasks = len(tasks)

    def _abandon(self) -> None:
        """Give up on the batch, as no caller is waiting for any of its keys.

        The batch is closed to new loads and its futures are cancelled, so
        that new loads of its keys start a new batch instead of waiting for
        this one.
        """
        self._abandoned = True
        self.dispatched = True
        for task in self.tasks:
            if not task.future.done():
                task.future.cancel()

    def _on_task_cancelled(self) -> None:
        self._live_tasks -= 1
        # Cancel the dispatch task if no caller is waiting for the batch.
        if (
            self._live_tasks == 0
            and not self._abandoned
            and self._dispatch_task is not None
            and not self._dispatch_task.done()
        ):
            self._abandon()
            self._dispatch_task.cancel()

    def __len__(self) -> int:
        return len(self.tasks)


class AbstractCache(ABC, Generic[K, T]):
    @abstractmethod
    def get(self, key: K) -> Future[T] | None:
        pass

    @abstractmethod
    def set(self, key: K, value: Future[T]) -> None:
        pass

    @abstractmethod
    def delete(self, key: K) -> None:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass


class DefaultCache(AbstractCache[K, T]):
    def __init__(self, cache_key_fn: Callable[[K], Hashable] | None = None) -> None:
        self.cache_key_fn: Callable[[K], Hashable] = (
            cache_key_fn if cache_key_fn is not None else lambda x: x
        )
        self.cache_map: dict[Hashable, Future[T]] = {}

    def get(self, key: K) -> Future[T] | None:
        return self.cache_map.get(self.cache_key_fn(key))

    def set(self, key: K, value: Future[T]) -> None:
        self.cache_map[self.cache_key_fn(key)] = value

    def delete(self, key: K) -> None:
        del self.cache_map[self.cache_key_fn(key)]

    def clear(self) -> None:
        self.cache_map.clear()


class DataLoader(Generic[K, T]):
    batch: Batch[K, T] | None = None
    cache: bool = False
    cache_map: AbstractCache[K, T]

    @overload
    def __init__(
        self,
        # any BaseException is rethrown in 'load', so should be excluded from the T type
        load_fn: Callable[[list[K]], Awaitable[Sequence[T | BaseException]]],
        max_batch_size: int | None = None,
        cache: bool = True,
        loop: AbstractEventLoop | None = None,
        cache_map: AbstractCache[K, T] | None = None,
        cache_key_fn: Callable[[K], Hashable] | None = None,
    ) -> None: ...

    # fallback if load_fn is untyped and there's no other info for inference
    @overload
    def __init__(
        self: DataLoader[K, Any],
        load_fn: Callable[[list[K]], Awaitable[list[Any]]],
        max_batch_size: int | None = None,
        cache: bool = True,
        loop: AbstractEventLoop | None = None,
        cache_map: AbstractCache[K, T] | None = None,
        cache_key_fn: Callable[[K], Hashable] | None = None,
    ) -> None: ...

    def __init__(  # noqa: PLR0917
        self,
        load_fn: Callable[[list[K]], Awaitable[Sequence[T | BaseException]]],
        max_batch_size: int | None = None,
        cache: bool = True,
        loop: AbstractEventLoop | None = None,
        cache_map: AbstractCache[K, T] | None = None,
        cache_key_fn: Callable[[K], Hashable] | None = None,
    ):
        self.load_fn = load_fn
        self.max_batch_size = max_batch_size

        self._loop = loop

        self.cache = cache

        if self.cache:
            self.cache_map = (
                DefaultCache(cache_key_fn) if cache_map is None else cache_map
            )

    @property
    def loop(self) -> AbstractEventLoop:
        if self._loop is None:
            self._loop = get_event_loop()

        return self._loop

    def load(self, key: K) -> Awaitable[T]:
        if not self.cache:
            uncached = self.loop.create_future()
            get_current_batch(self).add_task(key, uncached)
            return uncached

        cached = self.cache_map.get(key)

        if cached and not cached.cancelled():
            if cached.done():
                return cached

            if isinstance(cached, _CachedFuture) and cached.task is not None:
                return cached.task.add_waiter(self.loop)

            # Not created by a loader: give the caller its own future, so
            # that cancelling it doesn't cancel the one shared by the others.
            return _follow(cached, self.loop)

        future: _CachedFuture[T] = _CachedFuture(loop=self.loop)
        future.task = None
        # Cache the future first, so that nothing is loaded if this fails
        self.cache_map.set(key, future)

        task = get_current_batch(self).add_task(key, future)
        future.task = task

        return task.add_waiter(self.loop)

    def load_many(self, keys: Iterable[K]) -> Awaitable[list[T]]:
        return gather(*map(self.load, keys))

    def clear(self, key: K) -> None:
        if self.cache:
            self.cache_map.delete(key)

    def clear_many(self, keys: Iterable[K]) -> None:
        if self.cache:
            for key in keys:
                self.cache_map.delete(key)

    def clear_all(self) -> None:
        if self.cache:
            self.cache_map.clear()

    def prime(self, key: K, value: T, force: bool = False) -> None:
        self.prime_many({key: value}, force)

    def prime_many(self, data: Mapping[K, T], force: bool = False) -> None:
        # Populate the cache with the specified values
        if self.cache:
            for key, value in data.items():
                if not self.cache_map.get(key) or force:
                    future: Future = Future(loop=self.loop)
                    future.set_result(value)
                    self.cache_map.set(key, future)

        # For keys that are pending on the current batch, but the
        # batch hasn't started fetching yet: Remove it from the
        # batch and set to the specified value
        if self.batch is not None and not self.batch.dispatched:
            batch_updated = False
            for task in self.batch.tasks:
                if task.key in data:
                    batch_updated = True
                    task.set_result(data[task.key])
            if batch_updated:
                self.batch._remove_done_tasks()


def _follow(source: Future[T], loop: AbstractEventLoop) -> Future[T]:
    """Return a new future resolved like `source`.

    Cancelling the new future doesn't cancel `source`.
    """
    waiter: Future[T] = loop.create_future()

    def copy_state(source: Future[T]) -> None:
        if waiter.done():
            return
        if source.cancelled():
            waiter.cancel()
        elif (exception := source.exception()) is not None:
            waiter.set_exception(exception)
        else:
            waiter.set_result(source.result())

    def on_waiter_done(waiter: Future[T]) -> None:
        if waiter.cancelled():
            source.remove_done_callback(copy_state)

    source.add_done_callback(copy_state)
    waiter.add_done_callback(on_waiter_done)
    return waiter


def should_create_new_batch(loader: DataLoader, batch: Batch) -> bool:
    return bool(
        batch.dispatched
        or (loader.max_batch_size and len(batch.tasks) >= loader.max_batch_size)
    )


def get_current_batch(loader: DataLoader) -> Batch:
    batch = loader.batch
    if batch is not None and batch.tasks and not should_create_new_batch(loader, batch):
        return batch

    batch = loader.batch = Batch()

    dispatch(loader, batch)

    return batch


def dispatch(loader: DataLoader, batch: Batch) -> None:
    def _schedule() -> None:
        batch._dispatch_task = create_task(dispatch_batch(loader, batch))
        batch._dispatch_task.add_done_callback(
            lambda _: setattr(batch, "_dispatch_task", None)
        )

    loader.loop.call_soon(_schedule)


async def dispatch_batch(loader: DataLoader, batch: Batch) -> None:
    batch.dispatched = True

    keys = [task.key for task in batch.tasks]
    if len(keys) == 0:
        # Ensure batch is not empty
        # Unlikely, but could happen if the tasks are
        # overridden with preset values
        return

    # Skip the batch entirely if no caller is waiting for the results.
    # This avoids calling load_fn (e.g. a database query) for nothing.
    if all(task._is_abandoned for task in batch.tasks):
        batch._abandon()
        return

    # TODO: check if load_fn return an awaitable and it is a list

    try:
        values = await loader.load_fn(keys)
        values = list(values)

        if len(values) != len(batch):
            raise WrongNumberOfResultsReturned(  # noqa: TRY301
                expected=len(batch), received=len(values)
            )

        for task, value in zip(batch.tasks, values, strict=True):
            # Trying to set_result in a cancelled future would raise
            # asyncio.exceptions.InvalidStateError
            if task.future.cancelled():
                continue

            if isinstance(value, BaseException):
                task.set_exception(value)
            else:
                task.set_result(value)
    except Exception as e:  # noqa: BLE001
        for task in batch.tasks:
            if task.future.cancelled():
                continue
            task.set_exception(e)


__all__ = [
    "AbstractCache",
    "Batch",
    "DataLoader",
    "DefaultCache",
    "LoaderTask",
    "dispatch",
    "dispatch_batch",
    "get_current_batch",
    "should_create_new_batch",
]
