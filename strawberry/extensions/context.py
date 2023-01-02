import contextlib
import inspect
from abc import ABC
from asyncio import iscoroutinefunction
from typing import AsyncIterator, Callable, Iterator, List, Union

from strawberry.extensions import Extension
from strawberry.utils.await_maybe import AsyncIteratorOrIterator


class GeneratorsMapper:
    __slots__ = ("validators", "parsers")

    def __init__(self):
        self.validators: list[AsyncIteratorOrIterator[None]] = []
        self.parsers: list[AsyncIteratorOrIterator[None]] = []


class ExtensionContextManager(ABC):
    __slots__ = ("HOOK_NAME", "_generators", "_sync_generators")
    HOOK_NAME: str

    def __init__(self, extensions: List[Extension]):
        self._generators: List[AsyncIterator[None]] = []
        self._sync_generators: List[Iterator[None]] = []
        for extension in extensions:
            generator_or_func: Union[AsyncIteratorOrIterator, Callable] = getattr(
                extension, self.HOOK_NAME
            )
            if inspect.isgeneratorfunction(generator_or_func):
                self._sync_generators.append(generator_or_func())
            elif inspect.isasyncgenfunction(generator_or_func):
                self._generators.append(generator_or_func())
            # if it is just normal function make a fake generator:
            else:
                func = generator_or_func
                if iscoroutinefunction(func):

                    async def fake_gen():
                        await func()
                        yield

                    self._generators.append(fake_gen())
                else:

                    def fake_gen():
                        func()
                        yield

                    self._sync_generators.append(fake_gen())

    def sync_gen_enter(self) -> None:
        for gen in self._sync_generators:
            gen.__next__()

    def sync_gen_exit(self) -> None:
        for sync_generator in self._sync_generators:
            with contextlib.suppress(StopIteration):
                sync_generator.__next__()

    def __enter__(self):
        self.sync_gen_enter()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sync_gen_exit()

    async def __aenter__(self):
        self.sync_gen_enter()
        for gen in self._generators:
            await gen.__anext__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.sync_gen_exit()
        for gen in self._generators:
            with contextlib.suppress(StopAsyncIteration):
                await gen.__anext__()


class RequestContextManager(ExtensionContextManager):
    HOOK_NAME = Extension.on_request.__name__


class ValidationContextManager(ExtensionContextManager):
    HOOK_NAME = Extension.on_validate.__name__


class ParsingContextManager(ExtensionContextManager):
    HOOK_NAME = Extension.on_parse.__name__


class ExecutingContextManager(ExtensionContextManager):
    HOOK_NAME = Extension.on_execute.__name__
