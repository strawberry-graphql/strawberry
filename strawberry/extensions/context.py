from __future__ import annotations

import contextlib
import inspect
import types
import warnings
from asyncio import iscoroutinefunction
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    NamedTuple,
    Optional,
    Union,
)

from strawberry.extensions import SchemaExtension
from strawberry.utils.await_maybe import AwaitableOrValue, await_maybe

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator
    from types import TracebackType

    from strawberry.extensions.base_extension import Hook


class WrappedHook(NamedTuple):
    extension: SchemaExtension
    hook: Callable[
        ...,
        Union[
            contextlib.AbstractAsyncContextManager[None],
            contextlib.AbstractContextManager[None],
        ],
    ]
    is_async: bool


class ExtensionContextManagerBase:
    __slots__ = (
        "async_exit_stack",
        "default_hook",
        "deprecation_message",
        "exit_stack",
        "hooks",
    )

    def __init_subclass__(cls) -> None:
        cls.DEPRECATION_MESSAGE = (
            f"Event driven styled extensions for "
            f"{cls.LEGACY_ENTER} or {cls.LEGACY_EXIT}"
            f" are deprecated, use {cls.HOOK_NAME} instead"
        )

    HOOK_NAME: str
    DEPRECATION_MESSAGE: str
    LEGACY_ENTER: str
    LEGACY_EXIT: str

    def __init__(self, extensions: list[SchemaExtension]) -> None:
        self.hooks: list[WrappedHook] = []
        self.default_hook: Hook = getattr(SchemaExtension, self.HOOK_NAME)
        for extension in extensions:
            hook = self.get_hook(extension)
            if hook:
                self.hooks.append(hook)

    def get_hook(self, extension: SchemaExtension) -> Optional[WrappedHook]:
        on_start = getattr(extension, self.LEGACY_ENTER, None)
        on_end = getattr(extension, self.LEGACY_EXIT, None)

        is_legacy = on_start is not None or on_end is not None
        hook_fn: Optional[Hook] = getattr(type(extension), self.HOOK_NAME)
        hook_fn = hook_fn if hook_fn is not self.default_hook else None
        if is_legacy and hook_fn is not None:
            raise ValueError(
                f"{extension} defines both legacy and new style extension hooks for "
                "{self.HOOK_NAME}"
            )
        if is_legacy:
            warnings.warn(self.DEPRECATION_MESSAGE, DeprecationWarning, stacklevel=3)
            return self.from_legacy(extension, on_start, on_end)

        if hook_fn:
            if inspect.isgeneratorfunction(hook_fn):
                context_manager = contextlib.contextmanager(
                    types.MethodType(hook_fn, extension)
                )
                return WrappedHook(
                    extension=extension, hook=context_manager, is_async=False
                )

            if inspect.isasyncgenfunction(hook_fn):
                context_manager_async = contextlib.asynccontextmanager(
                    types.MethodType(hook_fn, extension)
                )
                return WrappedHook(
                    extension=extension, hook=context_manager_async, is_async=True
                )

            if callable(hook_fn):
                return self.from_callable(extension, hook_fn)

            raise ValueError(
                f"Hook {self.HOOK_NAME} on {extension} "
                f"must be callable, received {hook_fn!r}"
            )

        return None  # Current extension does not define a hook for this lifecycle stage

    @staticmethod
    def from_legacy(
        extension: SchemaExtension,
        on_start: Optional[Callable[[], None]] = None,
        on_end: Optional[Callable[[], None]] = None,
    ) -> WrappedHook:
        if iscoroutinefunction(on_start) or iscoroutinefunction(on_end):

            @contextlib.asynccontextmanager
            async def iterator() -> AsyncIterator:
                if on_start:
                    await await_maybe(on_start())

                yield

                if on_end:
                    await await_maybe(on_end())

            return WrappedHook(extension=extension, hook=iterator, is_async=True)

        @contextlib.contextmanager
        def iterator_async() -> Iterator[None]:
            if on_start:
                on_start()

            yield

            if on_end:
                on_end()

        return WrappedHook(extension=extension, hook=iterator_async, is_async=False)

    @staticmethod
    def from_callable(
        extension: SchemaExtension,
        func: Callable[[SchemaExtension], AwaitableOrValue[Any]],
    ) -> WrappedHook:
        if iscoroutinefunction(func):

            @contextlib.asynccontextmanager
            async def iterator() -> AsyncIterator[None]:
                await func(extension)
                yield

            return WrappedHook(extension=extension, hook=iterator, is_async=True)

        @contextlib.contextmanager  # type: ignore[no-redef]
        def iterator() -> Iterator[None]:
            func(extension)
            yield

        return WrappedHook(extension=extension, hook=iterator, is_async=False)

    def __enter__(self) -> None:
        self.exit_stack = contextlib.ExitStack()

        self.exit_stack.__enter__()

        for hook in self.hooks:
            if hook.is_async:
                raise RuntimeError(
                    f"SchemaExtension hook {hook.extension}.{self.HOOK_NAME} "
                    "failed to complete synchronously."
                )
            self.exit_stack.enter_context(hook.hook())  # type: ignore

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.exit_stack.__exit__(exc_type, exc_val, exc_tb)

    async def __aenter__(self) -> None:
        self.async_exit_stack = contextlib.AsyncExitStack()

        await self.async_exit_stack.__aenter__()

        for hook in self.hooks:
            if hook.is_async:
                await self.async_exit_stack.enter_async_context(hook.hook())  # type: ignore
            else:
                self.async_exit_stack.enter_context(hook.hook())  # type: ignore

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        await self.async_exit_stack.__aexit__(exc_type, exc_val, exc_tb)


class OperationContextManager(ExtensionContextManagerBase):
    HOOK_NAME = SchemaExtension.on_operation.__name__
    LEGACY_ENTER = "on_request_start"
    LEGACY_EXIT = "on_request_end"


class ValidationContextManager(ExtensionContextManagerBase):
    HOOK_NAME = SchemaExtension.on_validate.__name__
    LEGACY_ENTER = "on_validation_start"
    LEGACY_EXIT = "on_validation_end"


class ParsingContextManager(ExtensionContextManagerBase):
    HOOK_NAME = SchemaExtension.on_parse.__name__
    LEGACY_ENTER = "on_parsing_start"
    LEGACY_EXIT = "on_parsing_end"


class ExecutingContextManager(ExtensionContextManagerBase):
    HOOK_NAME = SchemaExtension.on_execute.__name__
    LEGACY_ENTER = "on_executing_start"
    LEGACY_EXIT = "on_executing_end"
