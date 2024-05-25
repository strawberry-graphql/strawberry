from functools import lru_cache
from typing import Iterator, Optional

from strawberry.extensions.base_extension import SchemaExtension
from strawberry.schema.execute import parse_document


class ParserCache(SchemaExtension):
    """
    Add LRU caching the parsing step during execution to improve performance.

    Example:

    >>> import strawberry
    >>> from strawberry.extensions import ParserCache
    >>>
    >>> schema = strawberry.Schema(
    ...     Query,
    ...     extensions=[
    ...         ParserCache(maxsize=100),
    ...     ]
    ... )

    Arguments:

    `maxsize: Optional[int]`
        Set the maxsize of the cache. If `maxsize` is set to `None` then the
        cache will grow without bound.
        More info: https://docs.python.org/3/library/functools.html#functools.lru_cache

    """

    def __init__(self, maxsize: Optional[int] = None) -> None:
        self.cached_parse_document = lru_cache(maxsize=maxsize)(parse_document)

    def on_parse(self) -> Iterator[None]:
        execution_context = self.execution_context

        execution_context.graphql_document = self.cached_parse_document(
            execution_context.query, **execution_context.parse_options
        )
        yield
