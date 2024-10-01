from __future__ import annotations

import contextlib
import inspect
import types
from asyncio import iscoroutinefunction
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncContextManager,
    AsyncIterator,
    Callable,
    ContextManager,
    Iterator,
    List,
    NamedTuple,
    Optional,
    Type,
    Union,
)

from strawberry.extensions import SchemaExtension
from strawberry.types.execution import ExecutionContext
from strawberry.utils.await_maybe import AwaitableOrValue

if TYPE_CHECKING:
    from types import TracebackType

    from strawberry.extensions.base_extension import Hook


class WrappedHook(NamedTuple):
    extension: SchemaExtension
    hook: Callable[
        [ExecutionContext], Union[AsyncContextManager[None], ContextManager[None]]
    ]
    is_async: bool


class ExtensionContextManagerBase:
    __slots__ = (
        "hooks",
        "async_exit_stack",
        "exit_stack",
        "execution_context",
    )

    HOOK_NAME: str
    DEFAULT_HOOK: Hook

    def __init_subclass__(cls) -> None:
        cls.DEFAULT_HOOK = getattr(SchemaExtension, cls.HOOK_NAME)

    def __init__(
        self, hooks: List[WrappedHook], execution_context: ExecutionContext
    ) -> None:
        self.hooks = hooks
        self.execution_context = execution_context

    @classmethod
    def get_hooks(cls, extensions: List[SchemaExtension]) -> List[WrappedHook]:
        hooks = []

        for extension in extensions:
            hook = cls.get_hook(extension)
            if hook:
                hooks.append(hook)

        return hooks

    @classmethod
    def get_hook(cls, extension: SchemaExtension) -> Optional[WrappedHook]:
        hook_fn: Optional[Hook] = getattr(type(extension), cls.HOOK_NAME)
        hook_fn = hook_fn if hook_fn is not cls.DEFAULT_HOOK else None

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
                return cls.from_callable(extension, hook_fn)

            raise ValueError(
                f"Hook {self.HOOK_NAME} on {extension} "
                f"must be callable, received {hook_fn!r}"
            )

        return None  # Current extension does not define a hook for this lifecycle stage

    @staticmethod
    def from_callable(
        extension: SchemaExtension,
        func: Callable[[SchemaExtension, ExecutionContext], AwaitableOrValue[Any]],
    ) -> WrappedHook:
        self_ = extension   
        if iscoroutinefunction(func):

            @contextlib.asynccontextmanager
            async def iterator(execution_context: ExecutionContext) -> AsyncIterator[None]:
                await func(self_, execution_context)
                yield

            return WrappedHook(extension=extension, hook=iterator, is_async=True)
        else:

            @contextlib.contextmanager
            def iterator(execution_context: ExecutionContext) -> Iterator[None]:
                func(self_, execution_context)
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
            else:
                self.exit_stack.enter_context(hook.hook(self.execution_context))

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.exit_stack.__exit__(exc_type, exc_val, exc_tb)

    async def __aenter__(self) -> None:
        self.async_exit_stack = contextlib.AsyncExitStack()

        await self.async_exit_stack.__aenter__()

        for hook in self.hooks:
            if hook.is_async:
                await self.async_exit_stack.enter_async_context(
                    hook.hook(self.execution_context)
                )  # type: ignore
            else:
                self.async_exit_stack.enter_context(hook.hook(self.execution_context))  # type: ignore

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        await self.async_exit_stack.__aexit__(exc_type, exc_val, exc_tb)


class OperationContextManager(ExtensionContextManagerBase):
    HOOK_NAME = SchemaExtension.on_operation.__name__


class ValidationContextManager(ExtensionContextManagerBase):
    HOOK_NAME = SchemaExtension.on_validate.__name__


class ParsingContextManager(ExtensionContextManagerBase):
    HOOK_NAME = SchemaExtension.on_parse.__name__


class ExecutingContextManager(ExtensionContextManagerBase):
    HOOK_NAME = SchemaExtension.on_execute.__name__
