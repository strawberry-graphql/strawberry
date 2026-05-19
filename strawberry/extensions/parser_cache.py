from collections.abc import Callable, Iterator
from functools import cache, lru_cache
from typing import Any

from graphql.language.parser import parse

from strawberry.extensions.base_extension import SchemaExtension


@cache
def _get_parse_cache(maxsize: int | None) -> Callable[..., Any]:
    # Shared LRU caches keyed by ``maxsize``. Multiple ``ParserCache`` instances
    # (e.g. a fresh one constructed per request via the factory pattern) reuse
    # the same wrapped ``parse`` so caching is effective across requests
    # without sharing extension instances.
    return lru_cache(maxsize=maxsize)(parse)


class ParserCache(SchemaExtension):
    """Add LRU caching the parsing step during execution to improve performance.

    Pass it as a factory; the LRU cache lives at module level and is keyed by
    ``maxsize``, so it is shared across every request and every schema that
    constructs a ``ParserCache`` with the same ``maxsize``.

    ```python
    import strawberry
    from strawberry.extensions import ParserCache

    schema = strawberry.Schema(
        Query,
        extensions=[lambda: ParserCache(maxsize=100)],
    )
    ```
    """

    def __init__(self, maxsize: int | None = None) -> None:
        """Initialize the ParserCache.

        Args:
            maxsize: Set the maxsize of the cache. If `maxsize` is set to `None` then the
                cache will grow without bound.
                More info: https://docs.python.org/3/library/functools.html#functools.lru_cache
        """
        super().__init__()
        self.cached_parse_document = _get_parse_cache(maxsize)

    def on_parse(self) -> Iterator[None]:
        execution_context = self.execution_context

        execution_context.graphql_document = self.cached_parse_document(
            execution_context.query, **execution_context.parse_options
        )
        yield


__all__ = ["ParserCache"]
