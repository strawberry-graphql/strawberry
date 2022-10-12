from typing import Sequence, Type

from graphql.error import GraphQLError

from strawberry.extensions import Extension


class MaskErrors(Extension):
    visible_errors: Sequence[Type[Exception]]
    error_message: str

    def __init__(
        self,
        visible_errors: Sequence[Type[Exception]],
        error_message: str = "Unexpected error.",
    ):
        self.visible_errors = visible_errors
        self.error_message = error_message

    def __call__(self, execution_context):
        self.execution_context = execution_context
        return self

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
                if not error.original_error:
                    processed_errors.append(error)
                else:
                    original_error = error.original_error

                    if not self.visible_errors:
                        # anonymise all errors
                        processed_errors.append(self.anonymise_error(error))
                    else:
                        for visible_error_cls in self.visible_errors:
                            if not isinstance(original_error, visible_error_cls):
                                processed_errors.append(self.anonymise_error(error))
                            else:
                                processed_errors.append(error)

            result.errors = processed_errors
