import contextlib
import inspect
import warnings
from asyncio import iscoroutinefunction
from typing import AsyncIterator, Callable, Iterator, List, NamedTuple, Optional, Union

from strawberry.extensions import Extension
from strawberry.utils.await_maybe import AsyncIteratorOrIterator, await_maybe


class IteratorContainer(NamedTuple):
    aiter: Optional[AsyncIterator[None]] = None
    iter: Optional[Iterator[None]] = None


class ExtensionContextManagerBase:
    __slots__ = ("_generators", "deprecation_message")
    HOOK_NAME: str
    deprecation_message: str
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
        warnings.warn(self.deprecation_message)
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

        self.deprecation_message = (
            f"Event driven styled extensions for "
            f"{self.LEGACY_ENTER} or {self.LEGACY_EXIT}"
            f" are deprecated, use {self.HOOK_NAME} instead"
        )
        for extension in extensions:
            # maybe it is a legacy extension, so find the old hooks first
            if not self._legacy_extension_compat(extension):
                generator_or_func: Union[AsyncIteratorOrIterator, Callable] = getattr(
                    extension, self.HOOK_NAME
                )
                if inspect.isgeneratorfunction(generator_or_func):
                    self._generators.append(IteratorContainer(iter=generator_or_func()))
                elif inspect.isasyncgenfunction(generator_or_func):
                    self._generators.append(
                        IteratorContainer(aiter=generator_or_func())
                    )
                # if it is just normal function make a fake generator:
                else:
                    func = generator_or_func
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
                await gen.aiter.__anext__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        with contextlib.suppress(StopAsyncIteration, StopIteration):
            for gen in self._generators:
                if gen.iter:
                    gen.iter.__next__()
                else:
                    await gen.aiter.__anext__()


class RequestContextManager(ExtensionContextManagerBase):
    HOOK_NAME = Extension.on_request.__name__
    LEGACY_ENTER = "on_request_start"
    LEGACY_EXIT = "on_request_end"


class ValidationContextManager(ExtensionContextManagerBase):
    HOOK_NAME = Extension.on_validate.__name__
    LEGACY_ENTER = "on_validation_start"
    LEGACY_EXIT = "on_validation_end"


class ParsingContextManager(ExtensionContextManagerBase):
    HOOK_NAME = Extension.on_parse.__name__
    LEGACY_ENTER = "on_parsing_start"
    LEGACY_EXIT = "on_parsing_end"


class ExecutingContextManager(ExtensionContextManagerBase):
    HOOK_NAME = Extension.on_execute.__name__
    LEGACY_ENTER = "on_executing_start"
    LEGACY_EXIT = "on_executing_end"
