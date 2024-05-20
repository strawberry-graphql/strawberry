from typing import Iterator

from strawberry.extensions.base_extension import SchemaExtension


class MaxTokensLimiter(SchemaExtension):
    """
    Add a validator to limit the number of tokens in a GraphQL document.

    Example:

    >>> import strawberry
    >>> from strawberry.extensions import MaxTokensLimiter
    >>>
    >>> schema = strawberry.Schema(
    ...     Query,
    ...     extensions=[
    ...         MaxTokensLimiter(max_token_count=1000)
    ...     ]
    ... )

    Arguments:

    `max_token_count: int`
        The maximum number of tokens allowed in a GraphQL document.

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
        self.max_token_count = max_token_count

    def on_operation(self) -> Iterator[None]:
        self.execution_context.parse_options["max_tokens"] = self.max_token_count
        yield
