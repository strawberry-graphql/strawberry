"""Cache interface and implementations for JIT-compiled queries.

This module provides a pluggable caching system that allows users to:
- Use built-in cache implementations (LRU, simple dict)
- Provide custom cache implementations (Redis, Memcached, etc.)
- Disable caching entirely

Example usage:
    # Built-in LRU cache (default)
    from strawberry.jit import compile_query, LRUCache

    cache = LRUCache(max_size=256)
    compiler = JITCompiler(schema, cache=cache)

    # Custom cache (Redis, etc.)
    class RedisCache(QueryCache):
        def get(self, key):
            return redis.get(f"jit:{key}")

        def set(self, key, value):
            redis.set(f"jit:{key}", value, ex=3600)

    cache = RedisCache()
    compiler = JITCompiler(schema, cache=cache)

    # No caching
    compiler = JITCompiler(schema, cache=None)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import TYPE_CHECKING, Any, Callable, Optional

if TYPE_CHECKING:
    pass


class QueryCache(ABC):
    """Abstract base class for query cache implementations.

    Implement this interface to provide custom caching behavior
    (Redis, Memcached, disk cache, etc.).
    """

    @abstractmethod
    def get(self, key: str) -> Optional[Callable]:
        """Retrieve a compiled query from the cache.

        Args:
            key: Cache key (typically hash of the query string)

        Returns:
            The compiled query function, or None if not in cache
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Callable) -> None:
        """Store a compiled query in the cache.

        Args:
            key: Cache key (typically hash of the query string)
            value: The compiled query function to cache
        """
        pass

    def clear(self) -> None:
        """Clear all entries from the cache.

        Optional method - implement if your cache supports clearing.
        """
        pass

    def stats(self) -> dict[str, Any]:
        """Return cache statistics.

        Optional method - implement if your cache tracks metrics.

        Returns:
            Dictionary with stats like hits, misses, size, etc.
        """
        return {}


class NoOpCache(QueryCache):
    """Cache that doesn't cache anything.

    Use this to explicitly disable caching:
        compiler = JITCompiler(schema, cache=NoOpCache())
    """

    def get(self, key: str) -> Optional[Callable]:
        """Always returns None (cache miss)."""
        return None

    def set(self, key: str, value: Callable) -> None:
        """Does nothing."""
        pass


class SimpleCache(QueryCache):
    """Simple unbounded dictionary cache.

    Warning: This cache grows without bounds and never evicts entries.
    Only use for development or when you know the query set is small.

    For production, use LRUCache instead.
    """

    def __init__(self) -> None:
        """Initialize an empty cache."""
        self._cache: dict[str, Callable] = {}
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Callable]:
        """Retrieve from cache, tracking hits/misses."""
        if key in self._cache:
            self._hits += 1
            return self._cache[key]
        self._misses += 1
        return None

    def set(self, key: str, value: Callable) -> None:
        """Store in cache without any eviction."""
        self._cache[key] = value

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def stats(self) -> dict[str, Any]:
        """Return cache statistics."""
        return {
            "type": "SimpleCache",
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": (
                self._hits / (self._hits + self._misses)
                if (self._hits + self._misses) > 0
                else 0.0
            ),
        }


class LRUCache(QueryCache):
    """LRU (Least Recently Used) cache with configurable maximum size.

    This is the recommended cache for production use. When the cache
    reaches max_size, the least recently used entry is evicted.

    Args:
        max_size: Maximum number of compiled queries to cache (default: 128)

    Example:
        cache = LRUCache(max_size=256)
        compiler = JITCompiler(schema, cache=cache)

        # Check cache performance
        print(cache.stats())
    """

    def __init__(self, max_size: int = 128) -> None:
        """Initialize LRU cache with maximum size.

        Args:
            max_size: Maximum number of entries before eviction starts
        """
        if max_size <= 0:
            raise ValueError("max_size must be positive")

        self._cache: OrderedDict[str, Callable] = OrderedDict()
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: str) -> Optional[Callable]:
        """Retrieve from cache and mark as recently used."""
        if key in self._cache:
            self._hits += 1
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return self._cache[key]
        self._misses += 1
        return None

    def set(self, key: str, value: Callable) -> None:
        """Store in cache, evicting LRU entry if at capacity."""
        if key in self._cache:
            # Update existing entry
            self._cache.move_to_end(key)
            self._cache[key] = value
        else:
            # Add new entry
            self._cache[key] = value

            # Evict LRU if over capacity
            if len(self._cache) > self._max_size:
                self._cache.popitem(last=False)  # Remove oldest
                self._evictions += 1

    def clear(self) -> None:
        """Clear all cached entries and reset statistics."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def stats(self) -> dict[str, Any]:
        """Return comprehensive cache statistics."""
        return {
            "type": "LRUCache",
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "hit_rate": (
                self._hits / (self._hits + self._misses)
                if (self._hits + self._misses) > 0
                else 0.0
            ),
        }


# Default cache factory
def default_cache() -> QueryCache:
    """Create the default cache implementation.

    Returns an LRUCache with 128 max entries. Users can override
    by passing cache= to JITCompiler.
    """
    return LRUCache(max_size=128)


__all__ = [
    "QueryCache",
    "NoOpCache",
    "SimpleCache",
    "LRUCache",
    "default_cache",
]
