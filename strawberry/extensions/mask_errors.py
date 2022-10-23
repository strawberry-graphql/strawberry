from typing import Callable, Optional

from graphql.error import GraphQLError

from strawberry.extensions import Extension
from strawberry.types import ExecutionContext


def default_should_mask_error(_) -> bool:
    # Mask all errors
    return True


class MaskErrors(Extension):
    should_mask_error: Callable[[GraphQLError], bool]
    error_message: str
    status_code_hook: Optional[Callable[[GraphQLError, ExecutionContext], None]]

    def __init__(
        self,
        should_mask_error: Callable[[GraphQLError], bool] = default_should_mask_error,
        error_message: str = "Unexpected error.",
        status_code_hook: Callable[[GraphQLError, ExecutionContext], None] = None,
    ):
        self.should_mask_error = should_mask_error
        self.error_message = error_message
        self.status_code_hook = status_code_hook

    def anonymise_error(self, error: GraphQLError) -> GraphQLError:
        return GraphQLError(
            message=self.error_message,
            nodes=error.nodes,
            source=error.source,
            positions=error.positions,
            path=error.path,
            original_error=None,
        )

    def on_request_end(self):
        result = self.execution_context.result
        if result and result.errors:
            processed_errors = []
            for error in result.errors:
                if self.should_mask_error(error):
                    processed_errors.append(self.anonymise_error(error))
                else:
                    processed_errors.append(error)
                if self.status_code_hook:
                    self.status_code_hook(error, self.execution_context)
            result.errors = processed_errors
