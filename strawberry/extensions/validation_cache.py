from collections.abc import Iterator
from functools import lru_cache

from strawberry.extensions.base_extension import SchemaExtension


class ValidationCache(SchemaExtension):
    """Add LRU caching the validation step during execution to improve performance.

    The cache lives on the extension instance, so for it to be effective across
    requests the same ``ValidationCache`` instance has to be reused. Use it as
    a pass-through factory that returns a singleton:

    ```python
    import strawberry
    from strawberry.extensions import ValidationCache

    validation_cache = ValidationCache(maxsize=100)
    schema = strawberry.Schema(
        Query,
        extensions=[lambda: validation_cache],
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
        from strawberry.schema.schema import validate_document

        self.cached_validate_document = lru_cache(maxsize=maxsize)(validate_document)

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
