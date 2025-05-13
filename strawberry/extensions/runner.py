from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any, Optional

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
        extensions: Optional[list[SchemaExtension]] = None,
    ) -> None:
        self.execution_context = execution_context
        self.extensions = extensions or []

    def operation(self) -> OperationContextManager:
        return OperationContextManager(self.extensions)

    def validation(self) -> ValidationContextManager:
        return ValidationContextManager(self.extensions)

    def parsing(self) -> ParsingContextManager:
        return ParsingContextManager(self.extensions)

    def executing(self) -> ExecutingContextManager:
        return ExecutingContextManager(self.extensions)

    def get_extensions_results_sync(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for extension in self.extensions:
            if inspect.iscoroutinefunction(extension.get_results):
                msg = "Cannot use async extension hook during sync execution"
                raise RuntimeError(msg)
            data.update(extension.get_results())  # type: ignore

        return data

    async def get_extensions_results(self, ctx: ExecutionContext) -> dict[str, Any]:
        data: dict[str, Any] = {}

        for extension in self.extensions:
            data.update(await await_maybe(extension.get_results()))

        data.update(ctx.extensions_results)
        return data
