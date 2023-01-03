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


class IteratorContainer(NamedTuple):
    aiter: Optional[AsyncIterator[None]] = None
    iter: Optional[Iterator[None]] = None


class ExtensionContextManagerBase:
    __slots__ = ("_generators", "deprecation_message")

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
        if not enter and not exit_:
            return False
        warnings.warn(self.DEPRECATION_MESSAGE)
        if enter:
            if iscoroutinefunction(enter):
                enter_async = True
        if exit_:
            if iscoroutinefunction(exit_):
                exit_async = True

        if enter_async or exit_async:

            async def legacy_generator():
                if enter:
                    await await_maybe(enter())
                yield
                if exit_:
                    await await_maybe(exit_())

            self._generators.append(IteratorContainer(aiter=legacy_generator()))
        else:

            def legacy_generator():
                if enter:
                    enter()
                yield
                if exit_:
                    exit_()

            self._generators.append(IteratorContainer(iter=legacy_generator()))
        return True

    def __init__(self, extensions: List[Extension]):

        self._generators: List[IteratorContainer] = []

        for extension in extensions:
            # maybe it is a legacy extension, so find the old hooks first
            if not self._legacy_extension_compat(extension):
                generator_or_func: Optional[
                    Union[AsyncIteratorOrIterator, Callable]
                ] = getattr(extension, self.HOOK_NAME, None)
                if not generator_or_func:
                    continue

                if inspect.isgeneratorfunction(generator_or_func):
                    self._generators.append(IteratorContainer(iter=generator_or_func()))
                elif inspect.isasyncgenfunction(generator_or_func):
                    self._generators.append(
                        IteratorContainer(aiter=generator_or_func())
                    )
                # if it is just normal function make a fake generator:
                else:
                    func: Callable[
                        [], AwaitableOrValue
                    ] = generator_or_func  # type: ignore
                    if iscoroutinefunction(func):

                        async def fake_gen():
                            await func()
                            yield

                        self._generators.append(IteratorContainer(aiter=fake_gen()))
                    else:

                        def fake_gen():
                            func()
                            yield

                        self._generators.append(IteratorContainer(iter=fake_gen()))

    def iter_gens(self):
        # Note: we can't create similar async version
        # because coroutines are not allowed to raise StopIteration
        for gen in self._generators:
            assert gen.iter
            gen.iter.__next__()

    def __enter__(self):
        self.iter_gens()

    def __exit__(self, exc_type, exc_val, exc_tb):
        with contextlib.suppress(StopIteration):
            self.iter_gens()

    async def __aenter__(self):
        for gen in self._generators:
            if gen.iter:
                gen.iter.__next__()
            else:
                assert gen.aiter
                await gen.aiter.__anext__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        with contextlib.suppress(StopAsyncIteration, StopIteration):
            for gen in self._generators:
                if gen.iter:
                    gen.iter.__next__()
                else:
                    assert gen.aiter
                    await gen.aiter.__anext__()


class RequestContextManager(ExtensionContextManagerBase):
    HOOK_NAME = _ExtensionHinter.on_operation.__name__
    LEGACY_ENTER = "on_request_start"
    LEGACY_EXIT = "on_request_end"


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
