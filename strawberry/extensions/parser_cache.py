from collections.abc import Iterator
from functools import lru_cache
from typing import Optional

from graphql.language.parser import parse

from strawberry.extensions.base_extension import SchemaExtension


class ParserCache(SchemaExtension):
    """Add LRU caching the parsing step during execution to improve performance.

    Example:

    ```python
    import strawberry
    from strawberry.extensions import ParserCache

    schema = strawberry.Schema(
        Query,
        extensions=[
            ParserCache(maxsize=100),
        ],
    )
    ```
    """

    def __init__(self, maxsize: Optional[int] = None) -> None:
        """Initialize the ParserCache.

        Args:
            maxsize: Set the maxsize of the cache. If `maxsize` is set to `None` then the
                cache will grow without bound.
                More info: https://docs.python.org/3/library/functools.html#functools.lru_cache
        """
        self.cached_parse_document = lru_cache(maxsize=maxsize)(parse)

    def on_parse(self) -> Iterator[None]:
        execution_context = self.execution_context

        execution_context.graphql_document = self.cached_parse_document(
            execution_context.query, **execution_context.parse_options
        )
        yield


__all__ = ["ParserCache"]
