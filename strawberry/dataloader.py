import dataclasses
from asyncio import create_task, get_event_loop
from asyncio.futures import Future
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Generic, List, Optional, TypeVar


T = TypeVar("T")
K = TypeVar("K")


@dataclass
class LoaderTask:
    key: Any
    future: Future


@dataclass
class Batch:
    tasks: List[LoaderTask] = dataclasses.field(default_factory=list)

    def add_task(self, key: Any, future: Future):
        task = LoaderTask(key, future)
        self.tasks.append(task)


class DataLoader(Generic[T, K]):
    queue: List[LoaderTask] = []
    batch: Optional[Batch] = None

    def __init__(self, load_fn: Callable):
        self.load_fn = load_fn

        self.loop = get_event_loop()

    def load(self, key: K) -> Awaitable:
        future = self.loop.create_future()

        batch = get_current_batch(self)
        batch.add_task(key, future)

        return future


def should_create_new_batch(batch: Batch) -> bool:
    return False


def get_current_batch(loader: DataLoader) -> Batch:

    if loader.batch and not should_create_new_batch(loader.batch):
        return loader.batch

    loader.batch = Batch()

    dispatch(loader, loader.batch)

    return loader.batch


def dispatch(loader: DataLoader, batch: Batch):
    async def dispatch():
        await dispatch_batch(loader, batch)

    loader.loop.call_soon(create_task, dispatch())


async def dispatch_batch(loader: DataLoader, batch: Batch) -> None:
    # TODO: set guards on batch so we don't redispatch a dispatched batch

    keys = [task.key for task in batch.tasks]

    # TODO: check if load_fn return an awaitable and it is a list
    # TODO: check size

    values = await loader.load_fn(keys)
    values = list(values)

    for task, value in zip(batch.tasks, values):
        task.future.set_result(value)
