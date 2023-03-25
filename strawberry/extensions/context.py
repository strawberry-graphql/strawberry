from __future__ import annotations

import contextlib
import inspect
import warnings
from asyncio import iscoroutinefunction
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Callable,
    Iterator,
    List,
    NamedTuple,
    Optional,
    Type,
    Union,
)

from strawberry.extensions import SchemaExtension
from strawberry.utils.await_maybe import AwaitableOrValue, await_maybe

if TYPE_CHECKING:
    from types import TracebackType

    from strawberry.extensions.base_extension import Hook


class WrappedHook(NamedTuple):
    extension: SchemaExtension
    initialized_hook: Union[AsyncIterator[None], Iterator[None]]
    is_async: bool


class ExtensionContextManagerBase:
    __slots__ = ("hooks", "deprecation_message", "default_hook")

    def __init_subclass__(cls):
        cls.DEPRECATION_MESSAGE = (
            f"Event driven styled extensions for "
            f"{cls.LEGACY_ENTER} or {cls.LEGACY_EXIT}"
            f" are deprecated, use {cls.HOOK_NAME} instead"
        )

    HOOK_NAME: str
    DEPRECATION_MESSAGE: str
    LEGACY_ENTER: str
    LEGACY_EXIT: str

    def __init__(self, extensions: List[SchemaExtension]):
        self.hooks: List[WrappedHook] = []
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
        elif is_legacy:
            warnings.warn(self.DEPRECATION_MESSAGE, DeprecationWarning, stacklevel=3)
            return self.from_legacy(extension, on_start, on_end)

        if hook_fn:
            if inspect.isgeneratorfunction(hook_fn):
                return WrappedHook(extension, hook_fn(extension), False)

            if inspect.isasyncgenfunction(hook_fn):
                return WrappedHook(extension, hook_fn(extension), True)

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

            async def iterator():
                if on_start:
                    await await_maybe(on_start())
                yield
                if on_end:
                    await await_maybe(on_end())

            hook = iterator()
            return WrappedHook(extension, hook, True)

        else:

            def iterator():
                if on_start:
                    on_start()
                yield
                if on_end:
                    on_end()

            hook = iterator()
            return WrappedHook(extension, hook, False)

    @staticmethod
    def from_callable(
        extension: SchemaExtension,
        func: Callable[[SchemaExtension], AwaitableOrValue[Any]],
    ) -> WrappedHook:
        if iscoroutinefunction(func):

            async def async_iterator():
                await func(extension)
                yield

            hook = async_iterator()
            return WrappedHook(extension, hook, True)
        else:

            def iterator():
                func(extension)
                yield

            hook = iterator()
            return WrappedHook(extension, hook, False)

    def run_hooks_sync(self, is_exit: bool = False) -> None:
        """Run extensions synchronously."""
        ctx = (
            contextlib.suppress(StopIteration, StopAsyncIteration)
            if is_exit
            else contextlib.nullcontext()
        )
        for hook in self.hooks:
            with ctx:
                if hook.is_async:
                    raise RuntimeError(
                        f"SchemaExtension hook {hook.extension}.{self.HOOK_NAME} "
                        "failed to complete synchronously."
                    )
                else:
                    hook.initialized_hook.__next__()  # type: ignore[union-attr]

    async def run_hooks_async(self, is_exit: bool = False) -> None:
        """Run extensions asynchronously with support for sync lifecycle hooks.

        The ``is_exit`` flag is required as a `StopIteration` cannot be raised from
        within a coroutine.
        """
        ctx = (
            contextlib.suppress(StopIteration, StopAsyncIteration)
            if is_exit
            else contextlib.nullcontext()
        )

        for hook in self.hooks:
            with ctx:
                if hook.is_async:
                    await hook.initialized_hook.__anext__()  # type: ignore[union-attr]
                else:
                    hook.initialized_hook.__next__()  # type: ignore[union-attr]

    def __enter__(self):
        self.run_hooks_sync()

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ):
        self.run_hooks_sync(is_exit=True)

    async def __aenter__(self):
        await self.run_hooks_async()

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ):
        await self.run_hooks_async(is_exit=True)


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
