"""Optimized is_awaitable implementation for GraphQL execution.

This module provides a highly optimized is_awaitable function that adds a fast path
for common synchronous types, significantly improving performance when dealing with
large result sets containing primitive values.
"""

from __future__ import annotations

from inspect import CO_ITERABLE_COROUTINE
from types import CoroutineType, GeneratorType
from typing import Any

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
    - Checks other types directly, preserving graphql-core's check order

    Args:
        value: The value to check

    Returns:
        True if the value is awaitable, False otherwise
    """
    # Fast path: check if the type is a known non-awaitable type
    if type(value) in _NON_AWAITABLE_TYPES:
        return False

    # Keep graphql-core's order: isinstance can access a custom __class__, and
    # hasattr can invoke a descriptor. Reordering changes their side effects.
    return (
        isinstance(value, CoroutineType)
        or (
            isinstance(value, GeneratorType)
            and bool(value.gi_code.co_flags & CO_ITERABLE_COROUTINE)
        )
        or hasattr(value, "__await__")
    )
