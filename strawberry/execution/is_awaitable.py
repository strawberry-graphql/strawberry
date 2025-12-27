"""Optimized is_awaitable implementation for GraphQL execution.

This module provides a highly optimized is_awaitable function that adds a fast path
for common synchronous types, significantly improving performance when dealing with
large result sets containing primitive values.
"""

from __future__ import annotations

import inspect
from types import CoroutineType, GeneratorType
from typing import Any

__all__ = ["optimized_is_awaitable"]

CO_ITERABLE_COROUTINE = inspect.CO_ITERABLE_COROUTINE

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
    - Falls back to standard checks for other types
    - Avoids expensive isinstance and hasattr calls for common types

    Args:
        value: The value to check

    Returns:
        True if the value is awaitable, False otherwise
    """
    # Fast path: check if the type is a known non-awaitable type
    # This single check replaces 3 checks (isinstance, isinstance, hasattr)
    # for the most common case
    value_type = type(value)
    if value_type in _NON_AWAITABLE_TYPES:
        return False

    # For other types, use the standard graphql-core logic
    # This handles coroutines, generators, and custom awaitable objects
    return (
        # check for coroutine objects
        isinstance(value, CoroutineType)
        # check for old-style generator based coroutine objects
        or (
            isinstance(value, GeneratorType)
            and bool(value.gi_code.co_flags & CO_ITERABLE_COROUTINE)
        )
        # check for other awaitables (e.g. futures)
        or hasattr(value, "__await__")
    )
