from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any, Dict, List, Optional, cast

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
    extensions: List[SchemaExtension]

    def __init__(
        self,
        extensions: Optional[List[SchemaExtension]] = None,
    ) -> None:
        self.extensions = extensions or []
        self.operation_hooks = OperationContextManager.get_hooks(self.extensions)
        self.validation_hooks = ValidationContextManager.get_hooks(self.extensions)
        self.parsing_hooks = ParsingContextManager.get_hooks(self.extensions)
        self.executing_hooks = ExecutingContextManager.get_hooks(self.extensions)

    def operation(self, execution_context: ExecutionContext) -> OperationContextManager:
        return OperationContextManager(self.operation_hooks, execution_context)

    def validation(
        self, execution_context: ExecutionContext
    ) -> ValidationContextManager:
        return ValidationContextManager(self.validation_hooks, execution_context)

    def parsing(self, execution_context: ExecutionContext) -> ParsingContextManager:
        return ParsingContextManager(self.parsing_hooks, execution_context)

    def executing(self, execution_context: ExecutionContext) -> ExecutingContextManager:
        return ExecutingContextManager(self.executing_hooks, execution_context)

    def get_extensions_results_sync(
        self, execution_context: ExecutionContext
    ) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        for extension in self.extensions:
            if inspect.iscoroutinefunction(extension.get_results):
                msg = "Cannot use async extension hook during sync execution"
                raise RuntimeError(msg)
            data.update(cast(Dict[str, Any], extension.get_results(execution_context)))

        return data

    async def get_extensions_results(
        self, execution_context: ExecutionContext
    ) -> Dict[str, Any]:
        data: Dict[str, Any] = {}

        for extension in self.extensions:
            data.update(await await_maybe(extension.get_results(execution_context)))

        data.update(execution_context.extensions_results)
        return data
