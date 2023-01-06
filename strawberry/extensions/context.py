import contextlib
import inspect
import warnings
from asyncio import iscoroutinefunction
from typing import AsyncIterator, Callable, Iterator, List, NamedTuple, Optional, Union

from strawberry.extensions import Extension
from strawberry.extensions.base_extension import _ExtensionHinter
from strawberry.utils.await_maybe import (
    AsyncIteratorOrIterator,
    AwaitableOrValue,
    await_maybe,
)


class ExecutionStepInitialized(NamedTuple):
    async_iterables: List[AsyncIterator[None]]
    iterables: List[Iterator[None]]


class ExecutionStep(NamedTuple):
    async_iterables: List[Callable[[], AsyncIterator[None]]]
    iterables: List[Callable[[], Iterator[None]]]


class ExecutionOrderManager:
    def __init__(self):
        self.steps: List[ExecutionStep] = []

    def add(
        self,
        iterable: Optional[Callable[[], Iterator[None]]] = None,
        async_iterable: Optional[Callable[[], AsyncIterator[None]]] = None,
    ):
        try:
            previous_step = self.steps[-1]
        except IndexError:
            previous_step = ExecutionStep([], [])

        if async_iterable:
            if previous_step.async_iterables:
                previous_step.async_iterables.append(async_iterable)
            else:
                self.steps.append(
                    ExecutionStep(async_iterables=[async_iterable], iterables=[])
                )
        else:
            assert iterable
            if previous_step.iterables:
                previous_step.iterables.append(iterable)
            else:
                self.steps.append(
                    ExecutionStep(iterables=[iterable], async_iterables=[])
                )

    def initialized(self) -> List[ExecutionStepInitialized]:
        ret: List[ExecutionStepInitialized] = []
        for step in self.steps:
            initialized = ExecutionStepInitialized([], [])
            for it in step.iterables:
                initialized.iterables.append(it())
            for async_iter in step.async_iterables:
                initialized.async_iterables.append(async_iter())
            ret.append(initialized)
        return ret


class ExtensionContextManagerBase:
    __slots__ = ("_initialized_steps", "_execution_order")

    def __init_subclass__(cls, **kwargs):
        cls.DEPRECATION_MESSAGE = (
            f"Event driven styled extensions for "
            f"{cls.LEGACY_ENTER} or {cls.LEGACY_EXIT}"
            f" are deprecated, use {cls.HOOK_NAME} instead"
        )

    HOOK_NAME: str
    DEPRECATION_MESSAGE: str
    LEGACY_ENTER: str
    LEGACY_EXIT: str

    def _legacy_extension_compat(self, extension: Extension) -> bool:
        """
        Returns: a flag if there was any legacy extension
        """
        enter = getattr(extension, self.LEGACY_ENTER, None)
        exit_ = getattr(extension, self.LEGACY_EXIT, None)
        enter_async = False
        exit_async = False
        if enter or exit_:
            warnings.warn(self.DEPRECATION_MESSAGE)
            if enter:
                if iscoroutinefunction(enter):
                    enter_async = True
            if exit_:  # pragma: no cover
                if iscoroutinefunction(exit_):
                    exit_async = True

            if enter_async or exit_async:

                async def legacy_generator():
                    if enter:  # pragma: no cover
                        await await_maybe(enter())
                    yield
                    if exit_:  # pragma: no cover
                        await await_maybe(exit_())

                self._execution_order.add(async_iterable=legacy_generator)
            else:

                def legacy_generator():
                    if enter:
                        enter()
                    yield
                    if exit_:  # pragma: no cover
                        exit_()

                self._execution_order.add(iterable=legacy_generator)
            return True
        return False

    def __init__(self, extensions: List[Extension]):
        self._execution_order: ExecutionOrderManager = ExecutionOrderManager()
        self._initialized_steps: List[ExecutionStepInitialized]
        for extension in extensions:
            # maybe it is a legacy extension, so find the old hooks first
            if not self._legacy_extension_compat(extension):
                generator_or_func: Optional[
                    Union[AsyncIteratorOrIterator, Callable]
                ] = getattr(extension, self.HOOK_NAME, None)
                if not generator_or_func:
                    continue

                if inspect.isasyncgenfunction(generator_or_func):
                    self._execution_order.add(async_iterable=generator_or_func)

                elif inspect.isgeneratorfunction(generator_or_func):
                    self._execution_order.add(iterable=generator_or_func)
                # if it is just normal function make a fake generator:
                else:
                    func: Callable[
                        [], AwaitableOrValue
                    ] = generator_or_func  # type: ignore
                    if iscoroutinefunction(func):

                        async def fake_gen():
                            await func()
                            yield

                        self._execution_order.add(async_iterable=fake_gen)
                    else:

                        def fake_gen():
                            func()
                            yield

                        self._execution_order.add(iterable=fake_gen)

    def iter_gens(self):
        # Note: we can't create similar async version
        # because coroutines are not allowed to raise StopIteration
        for step in self._initialized_steps:
            for iterable in step.iterables:
                with contextlib.suppress(StopIteration):
                    iterable.__next__()

    def __enter__(self):
        self._initialized_steps = self._execution_order.initialized()
        self.iter_gens()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.iter_gens()
        self._initialized_steps = []

    async def __aenter__(self) -> None:
        self._initialized_steps = self._execution_order.initialized()
        for step in self._initialized_steps:
            for iterator in step.iterables:
                iterator.__next__()
            for async_iterator in step.async_iterables:
                await async_iterator.__anext__()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        for step in self._initialized_steps:
            for iterator in step.iterables:
                with contextlib.suppress(StopIteration):
                    iterator.__next__()
            for async_iterator in step.async_iterables:
                with contextlib.suppress(StopAsyncIteration):
                    await async_iterator.__anext__()
        self._initialized_steps = []

    async def exit(self, exc: Exception) -> None:
        await self.__aexit__(type(exc), exc.args, exc.__traceback__)


class OperationContextManager(ExtensionContextManagerBase):
    HOOK_NAME = _ExtensionHinter.on_operation.__name__
    LEGACY_ENTER = "on_request_start"
    LEGACY_EXIT = "on_request_end"

    async def __aenter__(self):
        await super().__aenter__()


class ValidationContextManager(ExtensionContextManagerBase):
    HOOK_NAME = _ExtensionHinter.on_validate.__name__
    LEGACY_ENTER = "on_validation_start"
    LEGACY_EXIT = "on_validation_end"


class ParsingContextManager(ExtensionContextManagerBase):
    HOOK_NAME = _ExtensionHinter.on_parse.__name__
    LEGACY_ENTER = "on_parsing_start"
    LEGACY_EXIT = "on_parsing_end"


class ExecutingContextManager(ExtensionContextManagerBase):
    HOOK_NAME = _ExtensionHinter.on_execute.__name__
    LEGACY_ENTER = "on_executing_start"
    LEGACY_EXIT = "on_executing_end"
