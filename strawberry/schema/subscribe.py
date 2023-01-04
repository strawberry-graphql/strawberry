from typing import AsyncGenerator, Optional

from graphql import ExecutionResult as OriginalExecutionResult
from graphql import subscribe as original_subscribe

from strawberry.schema.execute import AsyncExecutionBase
from strawberry.types import ExecutionResult


class Subscription(AsyncExecutionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial_execution_error: Optional[ExecutionResult] = None
        self.parsing_error: Optional[ExecutionResult] = None

        self.original_generator: Optional[
            AsyncGenerator[OriginalExecutionResult, None]
        ] = None

    async def subscribe(self) -> "Subscription":
        self.parsing_error = await self._parse_and_validate_runner()
        self.extensions_runner.operation().__aenter__()
        async_iterator_or_res = await original_subscribe(
            self.schema,
            self.execution_context.graphql_document,
            root_value=self.execution_context.root_value,
            variable_values=self.execution_context.variables,
            operation_name=self.execution_context.operation_name,
            context_value=self.execution_context.context,
        )
        if isinstance(async_iterator_or_res, ExecutionResult):
            self.initial_execution_error = self._handle_execution_result(
                result=async_iterator_or_res
            )
        else:
            self.original_generator = async_iterator_or_res
        return self

    def __aiter__(self) -> "Subscription":
        return self

    async def _collect_and_return(self, result: ExecutionResult) -> ExecutionResult:
        result.extensions = await self.extensions_runner.get_extensions_results()
        return result

    async def __anext__(self) -> ExecutionResult:
        if self.parsing_error:
            return await self._collect_and_return(self.parsing_error)
        if self.initial_execution_error:
            return await self._collect_and_return(self.initial_execution_error)
        # on the next loop raise stop flag
        if self.initial_execution_error or self.parsing_error:
            raise StopAsyncIteration
        assert self.original_generator
        async with self.extensions_runner.executing():
            if not self.execution_context.result:
                try:
                    result = await self.original_generator.__anext__()
                except StopAsyncIteration as exc:
                    await self.extensions_runner.operation().__aexit__()
                    raise exc
                ret = self._handle_execution_result(result=result)
            else:
                ret = self.execution_context.result
        return await self._collect_and_return(ret)

    async def terminate(self) -> None:
        await self.original_generator.aclose()
