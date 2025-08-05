from collections.abc import Iterator
from typing import Callable

from graphql.error import GraphQLError

from strawberry.extensions.base_extension import SchemaExtension


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

    def on_operation(self) -> Iterator[None]:
        yield

        pre_execution_errors = self.execution_context.pre_execution_errors or []
        self.execution_context.pre_execution_errors = self._process_errors(
            pre_execution_errors
        )

        result = self.execution_context.result

        if result is not None and result.errors:
            result.errors = self._process_errors(result.errors)


__all__ = ["MaskErrors"]
