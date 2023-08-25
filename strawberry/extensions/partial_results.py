from graphql import GraphQLError, located_error

from strawberry.extensions import SchemaExtension
from strawberry.utils.await_maybe import AsyncIteratorOrIterator


class PartialResultsExtension(SchemaExtension):
    """
    Allow returning partial results, with both:
    - non-null `data` field
    - non-empty `errors` array

    One powerful feature of GraphQL is returning both data AND errors
    The typical way to return an error in python graphql is to simply raise it,
    and let the library catch it and plumb through to a singleton `errors` array
    But this means we can't return data AND errors
    To work around this issue, this extension adds errors to the result after execution

    Note:
    Because these errors are not caught and formatted by the library,
    we lose some extra error metadata like locations and path, which can sometimes
    be auto-added for us in the errors array
    Users of this extension can optionally wrap their exceptions in a
    `GraphQLError` to add those fields themselves

    Usage:
    ```
    @strawberry.field
    def query(self, info: Info) -> bool:
        info.context.partial_errors.append(Exception("Partial failure"))
        return True
    ```
    """

    def on_execute(
        self,
    ) -> AsyncIteratorOrIterator[None]:
        """
        Before execution:
        - Initialize `partial_errors` to an empty list

        After execution:
        - Pull any errors off `partial_errors` and add them to
          the `result` as `GraphQLErrors`
        - To mirror existing library code, add to `execution_context` and process them
          since partial errors would otherwise get skipped
        """
        initial: list[Exception] = []
        if self.execution_context.context:
            self.execution_context.context.partial_errors = initial

        yield

        result = self.execution_context.result
        context = self.execution_context.context
        if result and context and context.partial_errors:
            # map all partial errors to `GraphQLError` if not one already
            partial_errors: list[GraphQLError] = [
                error if isinstance(error, GraphQLError) else located_error(error)
                for error in context.partial_errors
            ]

            # add partial errors to result's errors
            if not result.errors:
                result.errors = []
            result.errors.extend(partial_errors)

            # below block copied from `strawberry.schema.execute.execute(_sync)`
            # to mirror what was skipped in the library's execution
            # note that we set the execution context to ALL errors,
            # but only process the partial errors,
            # because all others were already processed

            # === begin block ===
            # Also set errors on the execution_context so that it's easier
            # to access in extensions
            self.execution_context.errors = result.errors
            # Run the `Schema.process_errors` function here before
            # extensions have a chance to modify them (see the MaskErrors
            # extension). That way we can log the original errors but
            # only return a sanitised version to the client.
            self.execution_context.schema.process_errors(
                partial_errors, self.execution_context
            )
            # === end block ===
