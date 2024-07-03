from __future__ import annotations

import inspect
import warnings
from typing import TYPE_CHECKING, Any, Dict, List, Optional

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
        execution_context: ExecutionContext,
        extensions: Optional[List[SchemaExtension]] = None,
    ) -> None:
        self.execution_context = execution_context
        self.extensions = extensions if extensions is not None else []

    def operation(self) -> OperationContextManager:
        return OperationContextManager(self.extensions, self.execution_context)

    def validation(self) -> ValidationContextManager:
        return ValidationContextManager(self.extensions, self.execution_context)

    def parsing(self) -> ParsingContextManager:
        return ParsingContextManager(self.extensions, self.execution_context)

    def executing(self) -> ExecutingContextManager:
        return ExecutingContextManager(self.extensions, self.execution_context)

    def get_extensions_results_sync(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {}

        for extension in self.extensions:
            if inspect.iscoroutinefunction(extension.get_results):
                msg = "Cannot use async extension hook during sync execution"
                raise RuntimeError(msg)

            data.update(extension.get_results())  # type: ignore

        return data

    async def get_extensions_results(self, ctx: ExecutionContext) -> Dict[str, Any]:
        data: Dict[str, Any] = {}

        for extension in self.extensions:
            if (get_results := extension.get_results) is not None:
                warnings.warn(
                    "get_results is deprecated, you can use the `execution_context.extensions_results` attribute instead",
                    DeprecationWarning,
                    stacklevel=2,
                )
                results = await await_maybe(get_results())
                data.update(results)

        data.update(ctx.extensions_results)
        return data
