from collections.abc import Callable, Iterator
from functools import lru_cache
from typing import Any

from graphql.language.parser import parse

from strawberry.extensions.base_extension import SchemaExtension

# Shared LRU caches keyed by ``maxsize``. Multiple ``ParserCache`` instances
# (e.g. a fresh one constructed per request via the factory pattern) reuse the
# same wrapped ``parse`` so caching is effective across requests without
# sharing extension instances.
_caches: dict[int | None, Callable[..., Any]] = {}


def _get_parse_cache(maxsize: int | None) -> Callable[..., Any]:
    cached = _caches.get(maxsize)
    if cached is None:
        cached = lru_cache(maxsize=maxsize)(parse)
        _caches[maxsize] = cached
    return cached


class ParserCache(SchemaExtension):
    """Add LRU caching the parsing step during execution to improve performance.

    Pass it as a factory; the LRU cache is shared across requests with the same
    ``maxsize`` so caching is effective even when a fresh extension is built per
    request.

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
