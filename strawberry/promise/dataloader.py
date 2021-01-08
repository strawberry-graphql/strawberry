import dataclasses
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Generic, List, Optional, TypeVar
from threading import local

from strawberry.exceptions import WrongNumberOfResultsReturned
from strawberry.promise import Promise, async_instance, default_scheduler


T = TypeVar("T")
K = TypeVar("K")


# Private: cached resolved Promise instance
cache = local()


def enqueue_post_promise_job(fn: Callable) -> None:
    global cache
    if not hasattr(cache, "resolved_promise"):
        cache.resolved_promise = Promise.resolve(None)

    def on_promise_resolve(v: Any) -> None:
        async_instance.invoke(fn, default_scheduler)

    cache.resolved_promise.then(on_promise_resolve)


@dataclass
class LoaderTask(Generic[K, T]):
    key: K
    resolve: Callable
    reject: Callable


@dataclass
class Batch(Generic[K, T]):
    tasks: List[LoaderTask] = dataclasses.field(default_factory=list)
    dispatched: bool = False

    def add_task(self, key: Any, resolve: Callable, reject: Callable):
        task = LoaderTask[K, T](key, resolve, reject)
        self.tasks.append(task)

    def __len__(self) -> int:
        return len(self.tasks)


class PromiseDataLoader(Generic[K, T]):
    batch: Optional[Batch[K, T]] = None
    cache: bool = False
    cache_map: Dict[K, Promise]

    def __init__(
        self,
        load_fn: Callable[[List[K]], Awaitable[List[T]]],
        max_batch_size: Optional[int] = None,
        cache: bool = True,
    ):
        self.load_fn = load_fn
        self.max_batch_size = max_batch_size

        self.cache = cache

        if self.cache:
            self.cache_map = {}

    def load(self, key: K) -> Promise[T]:
        if self.cache:
            future = self.cache_map.get(key)

            if future:
                return future

        def promise_callback(resolve, reject):
            batch = get_current_batch(self)
            batch.add_task(key, resolve, reject)

            enqueue_post_promise_job(lambda: dispatch_batch(self, batch))

        future = Promise(promise_callback)

        if self.cache:
            self.cache_map[key] = future

        return future


def should_create_new_batch(loader: PromiseDataLoader, batch: Batch) -> bool:
    if (
        batch.dispatched
        or loader.max_batch_size
        and len(batch) >= loader.max_batch_size
    ):
        return True

    return False


def get_current_batch(loader: PromiseDataLoader) -> Batch:
    if loader.batch and not should_create_new_batch(loader, loader.batch):
        return loader.batch

    loader.batch = Batch()

    return loader.batch


def dispatch_batch(loader: PromiseDataLoader, batch: Batch) -> None:
    # If the batch has already been dispatched then bail out
    if batch.dispatched is True:
        return

    batch.dispatched = True

    keys = [task.key for task in batch.tasks]

    # TODO: check if load_fn return an awaitable and it is a list

    try:
        batch_promise = loader.load_fn(keys)
    except Exception as e:
        for task in batch.tasks:
            task.reject(e)

        return None

    # Assert the expected response from load_fn
    if not batch_promise or not isinstance(batch_promise, Promise):
        # TODO
        error = TypeError(
            (
                "DataLoader must be constructed with a function which accepts "
                "Array<key> and returns Promise<Array<value>>, but the function did "
                "not return a Promise: {}."
            ).format(batch_promise)
        )
        for task in batch.tasks:
            task.reject(error)

        return None

    def batch_promise_resolved(values) -> None:
        # Assert the expected resolution from batchLoadFn.
        values = list(values)

        if len(values) != len(batch):
            raise WrongNumberOfResultsReturned(
                expected=len(batch), received=len(values)
            )

        # Step through the values, resolving or rejecting each Promise in the
        # loaded queue.
        for task, value in zip(batch.tasks, values):
            if isinstance(value, BaseException):
                task.reject(value)
            else:
                task.resolve(value)

    def batch_promise_failed(error: Exception) -> None:
        for task in batch.tasks:
            task.reject(error)

    batch_promise.then(batch_promise_resolved).catch(batch_promise_failed)
