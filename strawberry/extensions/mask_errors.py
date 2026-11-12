from collections.abc import Callable, Iterator
from contextvars import ContextVar
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


# This state belongs to one operation, not to the extension instance. A context
# variable keeps concurrent operations apart, also when the same instance serves
# more than one of them, and `on_operation` resets it when the operation ends.
_in_pre_execution_phase: ContextVar[bool] = ContextVar(
    "strawberry_mask_errors_in_pre_execution_phase", default=False
)
_stream_result_processed: ContextVar[bool] = ContextVar(
    "strawberry_mask_errors_stream_result_processed", default=False
)


class MaskErrors(SchemaExtension):
    should_mask_error: Callable[[GraphQLError], bool]
    error_message: str
    mask_pre_execution_errors: bool

    def __init__(
        self,
        should_mask_error: Callable[[GraphQLError], bool] = default_should_mask_error,
        error_message: str = "Unexpected error.",
        mask_pre_execution_errors: bool = True,
    ) -> None:
        """Initialize the MaskErrors extension.

        Args:
            should_mask_error: A function that tells if the extension must mask
                an error. Use the `original_error` attribute to examine the
                error that the resolver raised.
            error_message: The message that the client gets for a masked error.
            mask_pre_execution_errors: Mask the errors of the parse step and of
                the validation step. Set it to `False` to send the syntax errors
                and the validation errors of a document to the client. The
                extension continues to mask the errors of the execution step.
        """
        self.should_mask_error = should_mask_error
        self.error_message = error_message
        self.mask_pre_execution_errors = mask_pre_execution_errors

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

    @property
    def _masking_enabled(self) -> bool:
        """Return `True` if the extension must mask the errors of this phase.

        Parse errors and validation errors describe the document that the client
        sent, and they can show the shape of the schema. This is a different
        concern from the errors that resolvers raise. Thus the extension masks
        them only when `mask_pre_execution_errors` is `True`.
        """
        return self.mask_pre_execution_errors or not _in_pre_execution_phase.get()

    def _process_result(self, result: object) -> None:
        if isinstance(result, _ResultWithErrors) and result.errors:
            result.errors = self._process_errors(result.errors)

    def _process_stream_result(self, result: StreamExecutionResult) -> None:
        self._process_result(result)

        for incremental_result in getattr(result, "incremental", None) or ():
            self._process_result(incremental_result)

        for completed_result in getattr(result, "completed", None) or ():
            self._process_result(completed_result)

    def on_parse(self) -> Iterator[None]:
        _in_pre_execution_phase.set(True)
        yield

    def on_execute(self) -> Iterator[None]:
        # The parse step and the validation step always run before this hook.
        # Thus an operation that comes here did not fail in those steps.
        _in_pre_execution_phase.set(False)
        yield

    def on_operation(self) -> Iterator[None]:
        stream_token = _stream_result_processed.set(False)
        # An error that occurs before the parse step, a missing query for
        # example, does not come from the document. The extension always masks
        # these errors.
        phase_token = _in_pre_execution_phase.set(False)

        try:
            yield

            # Streaming operations are handled result-by-result before each
            # frame is yielded. Avoid processing the last result again when the
            # stream closes.
            if _stream_result_processed.get():
                return

            if not self._masking_enabled:
                return

            result = self.execution_context.result

            if isinstance(result, (GraphQLExecutionResult, StrawberryExecutionResult)):
                self._process_result(result)
            elif initial_result := getattr(result, "initial_result", None):
                self._process_result(initial_result)
        finally:
            # This state must not outlive the operation that set it.
            _in_pre_execution_phase.reset(phase_token)
            _stream_result_processed.reset(stream_token)

    def on_stream_result(self, result: StreamExecutionResult) -> Iterator[None]:
        """Mask errors before a streamed execution result reaches the client."""
        _stream_result_processed.set(True)

        if self._masking_enabled:
            self._process_stream_result(result)

        yield None
