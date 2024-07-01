from typing import Iterator

from strawberry.extensions.base_extension import SchemaExtension


class MaxTokensLimiter(SchemaExtension):
    """Add a validator to limit the number of tokens in a GraphQL document.

    Example:
    ```python
    import strawberry
    from strawberry.extensions import MaxTokensLimiter

    schema = strawberry.Schema(Query, extensions=[MaxTokensLimiter(max_token_count=1000)])
    ```

    The following things are counted as tokens:
    * various brackets: "{", "}", "(", ")"
    * colon :
    * words

    Not counted:
    * quotes
    """

    def __init__(
        self,
        max_token_count: int,
    ) -> None:
        """Initialize the MaxTokensLimiter.

        Args:
            max_token_count: The maximum number of tokens allowed in a GraphQL document.
        """
        self.max_token_count = max_token_count

    def on_operation(self) -> Iterator[None]:
        self.execution_context.parse_options["max_tokens"] = self.max_token_count
        yield


__all__ = ["MaxTokensLimiter"]
