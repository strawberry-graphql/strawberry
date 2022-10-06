import dataclasses
from abc import ABC, abstractmethod
from asyncio import create_task, gather, get_event_loop
from asyncio.events import AbstractEventLoop
from asyncio.futures import Future
from dataclasses import dataclass
from typing import (
    Any,
    Awaitable,
    Callable,
    Generic,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    TypeVar,
    Union,
    overload,
)

from .exceptions import WrongNumberOfResultsReturned


T = TypeVar("T")
K = TypeVar("K")


@dataclass
class LoaderTask(Generic[K, T]):
    key: K
    future: Future


@dataclass
class Batch(Generic[K, T]):
    tasks: List[LoaderTask] = dataclasses.field(default_factory=list)
    dispatched: bool = False

    def add_task(self, key: Any, future: Future):
        task = LoaderTask[K, T](key, future)
        self.tasks.append(task)

    def __len__(self) -> int:
        return len(self.tasks)


class AbstractCache(ABC):
    @abstractmethod
    def get(self, key: Any) -> Union[Any, None]:
        pass

    @abstractmethod
    def set(self, key: Any, value: Any) -> None:
        pass

    @abstractmethod
    def delete(self, key: Any) -> None:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass


class DefaultCache(AbstractCache):
    def __init__(self, cache_key_fn=None):
        if cache_key_fn:
            self.cache_key_fn = cache_key_fn
        else:
            self.cache_key_fn = lambda x: x

        self.cache_map = {}

    def get(self, key: K) -> T:
        return self.cache_map.get(self.cache_key_fn(key))

    def set(self, key: K, value: Any) -> None:
        self.cache_map[self.cache_key_fn(key)] = value

    def delete(self, key: K) -> None:
        del self.cache_map[self.cache_key_fn(key)]

    def clear(self):
        self.cache_map.clear()


class DataLoader(Generic[K, T]):
    batch: Optional[Batch[K, T]] = None
    cache: bool = False
    cache_map: AbstractCache

    @overload
    def __init__(
        self,
        # any BaseException is rethrown in 'load', so should be excluded from the T type
        load_fn: Callable[[List[K]], Awaitable[Sequence[Union[T, BaseException]]]],
        max_batch_size: Optional[int] = None,
        cache: bool = True,
        loop: AbstractEventLoop = None,
        cache_map: Optional[AbstractCache] = None,
        cache_key_fn: Optional[Callable[[K], Any]] = None,
    ) -> None:
        ...

    # fallback if load_fn is untyped and there's no other info for inference
    @overload
    def __init__(
        self: "DataLoader[K, Any]",
        load_fn: Callable[[List[K]], Awaitable[List[Any]]],
        max_batch_size: Optional[int] = None,
        cache: bool = True,
        loop: AbstractEventLoop = None,
        cache_map: Optional[AbstractCache] = None,
        cache_key_fn: Optional[Callable[[K], Any]] = None,
    ) -> None:
        ...

    def __init__(
        self,
        load_fn: Callable[[List[K]], Awaitable[Sequence[Union[T, BaseException]]]],
        max_batch_size: Optional[int] = None,
        cache: bool = True,
        loop: AbstractEventLoop = None,
        cache_map: Optional[AbstractCache] = None,
        cache_key_fn: Optional[Callable[[K], Any]] = None,
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
        if self.cache:
            future = self.cache_map.get(key)

            if future:
                return future

        future = self.loop.create_future()

        if self.cache:
            self.cache_map.set(key, future)

        batch = get_current_batch(self)
        batch.add_task(key, future)

        return future

    def load_many(self, keys: Iterable[K]) -> Awaitable[List[T]]:
        return gather(*map(self.load, keys))

    def clear(self, key: K):
        if self.cache:
            self.cache_map.delete(key)

    def clear_many(self, keys: Iterable[K]):
        if self.cache:
            for key in keys:
                self.cache_map.delete(key)

    def clear_all(self):
        if self.cache:
            self.cache_map.clear()

    def prime(self, key: K, value: T, force: bool = False):
        self.prime_many({key: value}, force)

    def prime_many(self, data: Mapping[K, T], force: bool = False):
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
                if task.key in data.keys():
                    batch_updated = True
                    task.future.set_result(data[task.key])
            if batch_updated:
                self.batch.tasks = [
                    task for task in self.batch.tasks if not task.future.done()
                ]


def should_create_new_batch(loader: DataLoader, batch: Batch) -> bool:
    if (
        batch.dispatched
        or loader.max_batch_size
        and len(batch) >= loader.max_batch_size
    ):
        return True

    return False


def get_current_batch(loader: DataLoader) -> Batch:
    if loader.batch and not should_create_new_batch(loader, loader.batch):
        return loader.batch

    loader.batch = Batch()

    dispatch(loader, loader.batch)

    return loader.batch


def dispatch(loader: DataLoader, batch: Batch):
    loader.loop.call_soon(create_task, dispatch_batch(loader, batch))


async def dispatch_batch(loader: DataLoader, batch: Batch) -> None:
    batch.dispatched = True

    keys = [task.key for task in batch.tasks]
    if len(keys) == 0:
        # Ensure batch is not empty
        # Unlikely, but could happen if the tasks are
        # overriden with preset values
        return

    # TODO: check if load_fn return an awaitable and it is a list

    try:
        values = await loader.load_fn(keys)
        values = list(values)

        if len(values) != len(batch):
            raise WrongNumberOfResultsReturned(
                expected=len(batch), received=len(values)
            )

        for task, value in zip(batch.tasks, values):
            if isinstance(value, BaseException):
                task.future.set_exception(value)
            else:
                task.future.set_result(value)
    except Exception as e:
        for task in batch.tasks:
            task.future.set_exception(e)
