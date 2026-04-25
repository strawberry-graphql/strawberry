from __future__ import annotations

import contextvars
from collections.abc import Callable
from enum import Enum
from typing import TYPE_CHECKING, Any

from strawberry.utils.await_maybe import AsyncIteratorOrIterator, AwaitableOrValue

if TYPE_CHECKING:
    from graphql import GraphQLResolveInfo

    from strawberry.types import ExecutionContext


class LifecycleStep(Enum):
    OPERATION = "operation"
    VALIDATION = "validation"
    PARSE = "parse"
    RESOLVE = "resolve"


# The currently-running request's ``ExecutionContext``. Set by the schema at
# the start of every ``execute`` / ``execute_sync`` / ``subscribe`` call and
# read via :attr:`SchemaExtension.execution_context`. Using a context variable
# keeps a single shared extension instance safe under concurrent execution
# (asyncio.gather, threaded ``execute_sync``) — each task/thread observes its
# own request's context. See issue #4369.
execution_context_var: contextvars.ContextVar[ExecutionContext | None] = (
    contextvars.ContextVar("strawberry.extension.execution_context", default=None)
)


class SchemaExtension:
    # to support extensions that still use the old signature
    # we have an optional argument here for ease of initialization.
    def __init__(
        self, *, execution_context: ExecutionContext | None = None
    ) -> None: ...

    @property
    def execution_context(self) -> ExecutionContext:
        """The currently-running request's :class:`ExecutionContext`.

        Backed by a context variable, so concurrent requests sharing this
        extension instance each see their own context. Accessing this outside
        an extension lifecycle hook raises ``RuntimeError``.
        """
        ec = execution_context_var.get()
        if ec is None:
            raise RuntimeError(
                "ExecutionContext is only available inside an extension "
                "lifecycle hook (on_operation, on_validate, on_parse, "
                "on_execute, resolve, get_results)."
            )
        return ec

    @execution_context.setter
    def execution_context(self, value: ExecutionContext) -> None:
        # Backwards-compat setter for code that does
        # ``self.execution_context = ec`` (notably older third-party
        # extensions). Updates the context variable so reads see the new value
        # within the current task/thread.
        execution_context_var.set(value)

    def on_operation(  # type: ignore
        self,
    ) -> AsyncIteratorOrIterator[None]:  # pragma: no cover
        """Called before and after a GraphQL operation (query / mutation) starts."""
        yield None

    def on_validate(  # type: ignore
        self,
    ) -> AsyncIteratorOrIterator[None]:  # pragma: no cover
        """Called before and after the validation step."""
        yield None

    def on_parse(  # type: ignore
        self,
    ) -> AsyncIteratorOrIterator[None]:  # pragma: no cover
        """Called before and after the parsing step."""
        yield None

    def on_execute(  # type: ignore
        self,
    ) -> AsyncIteratorOrIterator[None]:  # pragma: no cover
        """Called before and after the execution step."""
        yield None

    def resolve(
        self,
        _next: Callable,
        root: Any,
        info: GraphQLResolveInfo,
        *args: str,
        **kwargs: Any,
    ) -> AwaitableOrValue[object]:
        return _next(root, info, *args, **kwargs)

    def get_results(self) -> AwaitableOrValue[dict[str, Any]]:
        return {}

    @classmethod
    def _implements_resolve(cls) -> bool:
        """Whether the extension implements the resolve method."""
        return cls.resolve is not SchemaExtension.resolve


Hook = Callable[[SchemaExtension], AsyncIteratorOrIterator[None]]

HOOK_METHODS: set[str] = {
    SchemaExtension.on_operation.__name__,
    SchemaExtension.on_validate.__name__,
    SchemaExtension.on_parse.__name__,
    SchemaExtension.on_execute.__name__,
}

__all__ = [
    "HOOK_METHODS",
    "Hook",
    "LifecycleStep",
    "SchemaExtension",
    "execution_context_var",
]
