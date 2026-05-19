from collections.abc import Callable, Iterator
from functools import cache, lru_cache
from typing import Any

from strawberry.extensions.base_extension import SchemaExtension


@cache
def _get_validate_cache(maxsize: int | None) -> Callable[..., Any]:
    # Shared LRU caches keyed by ``maxsize``. Multiple ``ValidationCache``
    # instances (e.g. a fresh one per request via the factory pattern) reuse
    # the same wrapped ``validate_document`` so caching is effective across
    # requests without sharing extension instances.
    # ``validate_document`` is imported lazily to break the circular import
    # with ``strawberry.schema.schema``.
    from strawberry.schema.schema import validate_document

    return lru_cache(maxsize=maxsize)(validate_document)


class ValidationCache(SchemaExtension):
    """Add LRU caching the validation step during execution to improve performance.

    Pass it as a factory; the LRU cache lives at module level and is keyed by
    ``maxsize``, so it is shared across every request and every schema that
    constructs a ``ValidationCache`` with the same ``maxsize``.

    ```python
    import strawberry
    from strawberry.extensions import ValidationCache

    schema = strawberry.Schema(
        Query,
        extensions=[lambda: ValidationCache(maxsize=100)],
    )
    ```
    """

    def __init__(self, maxsize: int | None = None) -> None:
        """Initialize the ValidationCache.

        Args:
            maxsize: Set the maxsize of the cache. If `maxsize` is set to `None` then the
                cache will grow without bound.

        More info: https://docs.python.org/3/library/functools.html#functools.lru_cache
        """
        super().__init__()
        self.cached_validate_document = _get_validate_cache(maxsize)

    def on_validate(self) -> Iterator[None]:
        execution_context = self.execution_context

        errors = self.cached_validate_document(
            execution_context.schema._schema,
            execution_context.graphql_document,
            execution_context.validation_rules,
        )
        execution_context.pre_execution_errors = errors
        yield


__all__ = ["ValidationCache"]
