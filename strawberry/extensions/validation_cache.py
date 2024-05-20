from functools import lru_cache
from typing import Iterator, Optional

from strawberry.extensions.base_extension import SchemaExtension
from strawberry.schema.execute import validate_document


class ValidationCache(SchemaExtension):
    """
    Add LRU caching the validation step during execution to improve performance.

    Example:

    >>> import strawberry
    >>> from strawberry.extensions import ValidationCache
    >>>
    >>> schema = strawberry.Schema(
    ...     Query,
    ...     extensions=[
    ...         ValidationCache(maxsize=100),
    ...     ]
    ... )

    Arguments:

    `maxsize: Optional[int]`
        Set the maxsize of the cache. If `maxsize` is set to `None` then the
        cache will grow without bound.
        More info: https://docs.python.org/3/library/functools.html#functools.lru_cache

    """

    def __init__(self, maxsize: Optional[int] = None) -> None:
        self.cached_validate_document = lru_cache(maxsize=maxsize)(validate_document)

    def on_validate(self) -> Iterator[None]:
        execution_context = self.execution_context

        errors = self.cached_validate_document(
            execution_context.schema._schema,
            execution_context.graphql_document,
            execution_context.validation_rules,
        )
        execution_context.errors = errors
        yield
