from collections.abc import Callable, Iterator
from typing import Protocol, runtime_checkable

from graphql import ExecutionResult as GraphQLExecutionResult
from graphql.error import GraphQLError

from strawberry.extensions.base_extension import SchemaExtension
from strawberry.types.execution import (
    ExecutionResult as StrawberryExecutionResult,
)
from strawberry.types.execution import StreamExecutionResult


@runtime_checkable
class _ResultWithErrors(Protocol):
    errors: list[GraphQLError] | None


def default_should_mask_error(_: GraphQLError) -> bool:
    # Mask all errors
    return True


class MaskErrors(SchemaExtension):
    should_mask_error: Callable[[GraphQLError], bool]
    error_message: str

    def __init__(
        self,
        should_mask_error: Callable[[GraphQLError], bool] = default_should_mask_error,
        error_message: str = "Unexpected error.",
    ) -> None:
        self.should_mask_error = should_mask_error
        self.error_message = error_message
        self._stream_result_processed = False

    def anonymise_error(self, error: GraphQLError) -> GraphQLError:
        return GraphQLError(
            message=self.error_message,
            nodes=error.nodes,
            source=error.source,
            positions=error.positions,
            path=error.path,
            original_error=None,
        )

    def _process_errors(self, errors: list[GraphQLError]) -> list[GraphQLError]:
        processed_errors: list[GraphQLError] = []

        for error in errors:
            if self.should_mask_error(error):
                processed_errors.append(self.anonymise_error(error))
            else:
                processed_errors.append(error)

        return processed_errors

    def _process_result(self, result: object) -> None:
        if isinstance(result, _ResultWithErrors) and result.errors:
            result.errors = self._process_errors(result.errors)

    def _process_stream_result(self, result: StreamExecutionResult) -> None:
        self._process_result(result)

        for incremental_result in getattr(result, "incremental", None) or ():
            self._process_result(incremental_result)

        for completed_result in getattr(result, "completed", None) or ():
            self._process_result(completed_result)

    def on_operation(self) -> Iterator[None]:
        self._stream_result_processed = False
        yield

        # Streaming operations are handled result-by-result before each frame is
        # yielded. Avoid processing the last result again when the stream closes.
        if self._stream_result_processed:
            return

        result = self.execution_context.result

        if isinstance(result, (GraphQLExecutionResult, StrawberryExecutionResult)):
            self._process_result(result)
        elif initial_result := getattr(result, "initial_result", None):
            self._process_result(initial_result)
        # Synchronous parsing and validation failures don't populate `result`.
        elif pre_execution_errors := self.execution_context.pre_execution_errors:
            self.execution_context.pre_execution_errors = self._process_errors(
                pre_execution_errors
            )

    def on_stream_result(self, result: StreamExecutionResult) -> Iterator[None]:
        """Mask errors before a streamed execution result reaches the client."""
        self._stream_result_processed = True
        self._process_stream_result(result)
        yield None
