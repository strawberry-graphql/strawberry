"""Optimized is_awaitable implementation for GraphQL execution.

This module provides a highly optimized is_awaitable function that adds a fast path
for common synchronous types, significantly improving performance when dealing with
large result sets containing primitive values.
"""

from __future__ import annotations

from typing import Any

from graphql.pyutils.is_awaitable import is_awaitable as graphql_core_is_awaitable

__all__ = ["optimized_is_awaitable"]

# Common synchronous types that are never awaitable
# Using a frozenset for O(1) lookup
_NON_AWAITABLE_TYPES: frozenset[type] = frozenset(
    {
        type(None),
        bool,
        int,
        float,
        str,
        bytes,
        bytearray,
        list,
        tuple,
        dict,
        set,
        frozenset,
    }
)


def optimized_is_awaitable(value: Any) -> bool:
    """Return true if object can be passed to an ``await`` expression.

    This is an optimized version of graphql-core's is_awaitable that adds a fast path
    for common synchronous types. For large result sets containing mostly primitive
    values (ints, strings, lists, etc.), this can provide significant performance
    improvements.

    Performance characteristics:
    - Fast path for primitives: O(1) type lookup
    - Falls back to graphql-core's is_awaitable for other types

    Args:
        value: The value to check

    Returns:
        True if the value is awaitable, False otherwise
    """
    # Fast path: check if the type is a known non-awaitable type
    if type(value) in _NON_AWAITABLE_TYPES:
        return False

    # Fallback to graphql-core's implementation for other types
    return graphql_core_is_awaitable(value)
