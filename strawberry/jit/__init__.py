"""JIT compiler for Strawberry GraphQL.

Provides compile-time optimizations for GraphQL queries with 5-6x performance improvement.

Example:
    >>> import strawberry
    >>> from strawberry.jit import compile_query
    >>>
    >>> @strawberry.type
    >>> class Query:
    >>>     @strawberry.field
    >>>     def hello(self) -> str:
    >>>         return "world"
    >>>
    >>> schema = strawberry.Schema(query=Query)
    >>> compiled = compile_query(schema, "query { hello }")
    >>> result = compiled(Query())
"""

from __future__ import annotations

from .cache import LRUCache, NoOpCache, QueryCache, SimpleCache
from .compiler import JITCompiler, compile_query

__all__ = [
    "JITCompiler",
    "compile_query",
    "QueryCache",
    "LRUCache",
    "SimpleCache",
    "NoOpCache",
]
