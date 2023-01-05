from typing import AsyncGenerator, Optional, Union

from graphql import ExecutionResult as OriginalExecutionResult
from graphql import subscribe as original_subscribe

from strawberry.schema.execute import AsyncExecutionBase
from strawberry.types import ExecutionResult
from strawberry.types.execution import ExecutionResultError


class Subscription(AsyncExecutionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._operation_cm = self.extensions_runner.operation()
        self._original_generator: Optional[
            AsyncGenerator[OriginalExecutionResult, None]
        ] = None

    async def subscribe(self) -> Union[ExecutionResultError, "Subscription"]:
        initial_error = await self._parse_and_validate_runner()
        generator_or_result = None
        if not initial_error:
            await self._operation_cm.__aenter__()
            generator_or_result = await original_subscribe(
                self.schema,
                self.execution_context.graphql_document,
                root_value=self.execution_context.root_value,
                variable_values=self.execution_context.variables,
                operation_name=self.execution_context.operation_name,
                context_value=self.execution_context.context,
            )

        # permission errors would return here.
        if isinstance(generator_or_result, OriginalExecutionResult):
            initial_error = ExecutionResultError(
                data=generator_or_result.data, errors=generator_or_result.errors
            )
        if initial_error:
            initial_error.extensions = (
                await self.extensions_runner.get_extensions_results()
            )
            return initial_error

        generator = generator_or_result
        # there should not be any validation errors so the result is async generator
        assert hasattr(generator, "__aiter__")
        self._original_generator = generator.__aiter__()
        return self

    def __aiter__(self) -> "Subscription":
        return self

    async def _collect_and_return(self, result: ExecutionResult) -> ExecutionResult:
        result.extensions = await self.extensions_runner.get_extensions_results()
        return result

    async def __anext__(self) -> ExecutionResult:
        assert self._original_generator
        # clean result on every iteration
        self.execution_context.result = None
        async with self.extensions_runner.executing():
            if not self.execution_context.result:

                try:
                    result = await self._original_generator.__anext__()
                except StopAsyncIteration as exc:
                    await self._operation_cm.exit(exc)
                    raise StopAsyncIteration from exc
                except Exception as exc:
                    await self._operation_cm.exit(exc)
                    raise exc

                ret = self._handle_execution_result(result=result)
            else:
                ret = self.execution_context.result
        return await self._collect_and_return(ret)

    async def aclose(self) -> None:
        await self._original_generator.aclose()
