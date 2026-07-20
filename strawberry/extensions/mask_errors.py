from collections.abc import Callable, Iterator
from typing import Any

from graphql.error import GraphQLError
from graphql.execution.execute import ExecutionResult as GraphQLExecutionResult

from strawberry.extensions.base_extension import SchemaExtension
from strawberry.types.execution import ExecutionResult as StrawberryExecutionResult


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

    # TODO: proper typing
    def _process_result(self, result: Any) -> None:
        if not result.errors:
            return

        processed_errors: list[GraphQLError] = []

        for error in result.errors:
            if self.should_mask_error(error):
                processed_errors.append(self.anonymise_error(error))
            else:
                processed_errors.append(error)

        result.errors = processed_errors

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
        elif result:
            self._process_result(result.initial_result)

    def on_stream_result(self, result: StrawberryExecutionResult) -> Iterator[None]:
        """Mask errors before a streamed execution result reaches the client."""
        self._stream_result_processed = True
        self._process_result(result)
        yield None
