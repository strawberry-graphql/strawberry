from __future__ import annotations

import contextlib
import inspect
import types
from asyncio import iscoroutinefunction
from typing import (
    TYPE_CHECKING,
    Any,
    NamedTuple,
)

from strawberry.extensions import SchemaExtension
from strawberry.extensions.base_extension import execution_context_var

if TYPE_CHECKING:
    import contextvars
    from collections.abc import AsyncIterator, Callable, Iterator
    from types import TracebackType

    from strawberry.extensions.base_extension import Hook
    from strawberry.types import ExecutionContext
    from strawberry.utils.await_maybe import AwaitableOrValue


class WrappedHook(NamedTuple):
    extension: SchemaExtension
    hook: Callable[
        ...,
        contextlib.AbstractAsyncContextManager[None]
        | contextlib.AbstractContextManager[None],
    ]
    is_async: bool


class ExtensionContextManagerBase:
    """Run extension lifecycle hooks and yield the bound ExecutionContext.

    Runs a single class of hooks (named by ``HOOK_NAME``) and yields the
    per-request ``ExecutionContext`` so callers can write
    ``with cm as execution_context:``. Subclasses just provide
    ``HOOK_NAME``. The only one that does extra work is
    :class:`OperationContextManager`, which additionally binds the
    per-request
    :data:`strawberry.extensions.base_extension.execution_context_var`
    so concurrent requests sharing one extension instance each see their
    own context.
    """

    __slots__ = (
        "async_exit_stack",
        "default_hook",
        "execution_context",
        "exit_stack",
        "hooks",
    )

    HOOK_NAME: str

    def __init__(
        self,
        extensions: list[SchemaExtension],
        execution_context: ExecutionContext,
    ) -> None:
        self.execution_context = execution_context
        self.hooks: list[WrappedHook] = []
        self.default_hook: Hook = getattr(SchemaExtension, self.HOOK_NAME)
        for extension in extensions:
            hook = self.get_hook(extension)
            if hook:
                self.hooks.append(hook)

    def get_hook(self, extension: SchemaExtension) -> WrappedHook | None:
        hook_fn: Hook | None = getattr(type(extension), self.HOOK_NAME)
        hook_fn = hook_fn if hook_fn is not self.default_hook else None

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

    def __enter__(self) -> ExecutionContext:
        self.exit_stack = contextlib.ExitStack()

        self.exit_stack.__enter__()

        for hook in self.hooks:
            if hook.is_async:
                raise RuntimeError(
                    f"SchemaExtension hook {hook.extension}.{self.HOOK_NAME} "
                    "failed to complete synchronously."
                )
            self.exit_stack.enter_context(hook.hook())  # type: ignore
        return self.execution_context

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.exit_stack.__exit__(exc_type, exc_val, exc_tb)

    async def __aenter__(self) -> ExecutionContext:
        self.async_exit_stack = contextlib.AsyncExitStack()

        await self.async_exit_stack.__aenter__()

        for hook in self.hooks:
            if hook.is_async:
                await self.async_exit_stack.enter_async_context(hook.hook())  # type: ignore
            else:
                self.async_exit_stack.enter_context(hook.hook())  # type: ignore
        return self.execution_context

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.async_exit_stack.__aexit__(exc_type, exc_val, exc_tb)


class OperationContextManager(ExtensionContextManagerBase):
    """Top-level extension context manager for a GraphQL operation.

    In addition to running the ``on_operation`` lifecycle hooks and
    yielding the ``ExecutionContext`` (inherited behaviour), it binds
    that context to the per-request
    :data:`strawberry.extensions.base_extension.execution_context_var`
    so concurrent requests sharing a single extension instance each
    see their own context (asyncio.gather, threaded ``execute_sync``).
    """

    __slots__ = ("_token",)

    HOOK_NAME = SchemaExtension.on_operation.__name__

    def __enter__(self) -> ExecutionContext:
        self._token: contextvars.Token | None = execution_context_var.set(
            self.execution_context
        )
        try:
            return super().__enter__()
        except BaseException:
            execution_context_var.reset(self._token)
            self._token = None
            raise

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        try:
            super().__exit__(exc_type, exc_val, exc_tb)
        finally:
            if self._token is not None:
                execution_context_var.reset(self._token)

    async def __aenter__(self) -> ExecutionContext:
        self._token = execution_context_var.set(self.execution_context)
        try:
            return await super().__aenter__()
        except BaseException:
            execution_context_var.reset(self._token)
            self._token = None
            raise

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        try:
            await super().__aexit__(exc_type, exc_val, exc_tb)
        finally:
            if self._token is not None:
                execution_context_var.reset(self._token)


class ValidationContextManager(ExtensionContextManagerBase):
    HOOK_NAME = SchemaExtension.on_validate.__name__


class ParsingContextManager(ExtensionContextManagerBase):
    HOOK_NAME = SchemaExtension.on_parse.__name__


class ExecutingContextManager(ExtensionContextManagerBase):
    HOOK_NAME = SchemaExtension.on_execute.__name__
