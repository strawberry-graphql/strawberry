import dataclasses
from asyncio import create_task, get_event_loop
from asyncio.events import AbstractEventLoop
from asyncio.futures import Future
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Generic, List, Optional, TypeVar

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

    def __init__(
        self,
        load_fn: Callable[[List[K]], Awaitable[List[T]]],
        max_batch_size: Optional[int] = None,
        cache: bool = True,
        loop: AbstractEventLoop = None,
    ):
        self.load_fn = load_fn
        self.max_batch_size = max_batch_size

        self.loop = loop or get_event_loop()

        self.cache = cache

        if self.cache:
            self.cache_map = {}

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
