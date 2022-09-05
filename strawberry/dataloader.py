import dataclasses
from asyncio import create_task, gather, get_event_loop
from asyncio.events import AbstractEventLoop
from asyncio.futures import Future
from dataclasses import dataclass
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Generic,
    Iterable,
    List,
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


class DataLoader(Generic[K, T]):
    queue: List[LoaderTask] = []
    batch: Optional[Batch[K, T]] = None
    cache: bool = False
    cache_map: Dict[K, Future]

    @overload
    def __init__(
        self,
        # any BaseException is rethrown in 'load', so should be excluded from the T type
        load_fn: Callable[[List[K]], Awaitable[Sequence[Union[T, BaseException]]]],
        max_batch_size: Optional[int] = None,
        cache: bool = True,
        loop: AbstractEventLoop = None,
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
    ) -> None:
        ...

    def __init__(
        self,
        load_fn: Callable[[List[K]], Awaitable[Sequence[Union[T, BaseException]]]],
        max_batch_size: Optional[int] = None,
        cache: bool = True,
        loop: AbstractEventLoop = None,
    ):
        self.load_fn = load_fn
        self.max_batch_size = max_batch_size

        self._loop = loop

        self.cache = cache

        if self.cache:
            self.cache_map = {}

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
            self.cache_map[key] = future

        batch = get_current_batch(self)
        batch.add_task(key, future)

        return future

    def load_many(self, keys: Iterable[K]) -> Awaitable[List[T]]:
        return gather(*map(self.load, keys))


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
    async def dispatch():
        await dispatch_batch(loader, batch)

    loader.loop.call_soon(create_task, dispatch())


async def dispatch_batch(loader: DataLoader, batch: Batch) -> None:
    batch.dispatched = True

    keys = [task.key for task in batch.tasks]

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
