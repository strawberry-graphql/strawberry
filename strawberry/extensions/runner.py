from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any

from strawberry.extensions.base_extension import execution_context_var
from strawberry.extensions.context import (
    ExecutingContextManager,
    OperationContextManager,
    ParsingContextManager,
    ValidationContextManager,
)
from strawberry.utils.await_maybe import await_maybe

if TYPE_CHECKING:
    from strawberry.types import ExecutionContext

    from . import SchemaExtension


class SchemaExtensionsRunner:
    extensions: list[SchemaExtension]

    def __init__(
        self,
        execution_context: ExecutionContext,
        extensions: list[SchemaExtension] | None = None,
    ) -> None:
        self.execution_context = execution_context
        self.extensions = extensions or []

    def operation(self) -> OperationContextManager:
        return OperationContextManager(self.extensions, self.execution_context)

    def validation(self) -> ValidationContextManager:
        return ValidationContextManager(self.extensions, self.execution_context)

    def parsing(self) -> ParsingContextManager:
        return ParsingContextManager(self.extensions, self.execution_context)

    def executing(self) -> ExecutingContextManager:
        return ExecutingContextManager(self.extensions, self.execution_context)

    def get_extensions_results_sync(self, ctx: ExecutionContext) -> dict[str, Any]:
        # ``get_results`` may be invoked after ``OperationContextManager`` has
        # already exited and reset the per-request ContextVar (e.g. for the
        # success path of ``execute_sync``, where the call sits *outside* the
        # ``with`` block so ``on_operation`` post-yield code can mutate the
        # result first). Bind the ContextVar locally so extensions can still
        # read ``self.execution_context`` regardless of the call site.
        token = execution_context_var.set(ctx)
        try:
            data: dict[str, Any] = {}
            for extension in self.extensions:
                if inspect.iscoroutinefunction(extension.get_results):
                    msg = "Cannot use async extension hook during sync execution"
                    raise RuntimeError(msg)
                data.update(extension.get_results())  # type: ignore

            data.update(ctx.extensions_results)
        finally:
            execution_context_var.reset(token)

        return data

    async def get_extensions_results(self, ctx: ExecutionContext) -> dict[str, Any]:
        # See ``get_extensions_results_sync`` for why we bind the ContextVar.
        token = execution_context_var.set(ctx)
        try:
            data: dict[str, Any] = {}

            for extension in self.extensions:
                data.update(await await_maybe(extension.get_results()))

            data.update(ctx.extensions_results)
        finally:
            execution_context_var.reset(token)

        return data
