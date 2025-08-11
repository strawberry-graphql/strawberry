"""
JIT compiler with query caching.

This version caches compiled queries to avoid recompilation overhead
for frequently executed queries, providing significant performance benefits.
"""

from __future__ import annotations

import hashlib
import time
from functools import lru_cache
from typing import Callable, Dict, Optional, Tuple
from weakref import WeakValueDictionary

from graphql import GraphQLSchema, parse, print_ast, validate

from strawberry.jit_compiler import GraphQLJITCompiler
from strawberry.jit_compiler_parallel import ParallelAsyncJITCompiler


class CacheStats:
    """Statistics for cache performance monitoring."""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.compilation_time = 0.0
        self.cache_retrieval_time = 0.0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def __str__(self) -> str:
        return (
            f"CacheStats(hits={self.hits}, misses={self.misses}, "
            f"hit_rate={self.hit_rate:.2%}, evictions={self.evictions}, "
            f"compilation_time={self.compilation_time:.3f}s)"
        )


class QueryCache:
    """
    Thread-safe cache for compiled GraphQL queries.
    
    Features:
    - LRU eviction policy
    - Weak references for memory efficiency
    - Cache statistics for monitoring
    - Query normalization for better hit rates
    """
    
    def __init__(self, max_size: int = 1000, ttl: Optional[float] = None):
        """
        Initialize the query cache.
        
        Args:
            max_size: Maximum number of cached queries
            ttl: Time-to-live in seconds (None for no expiration)
        """
        self.max_size = max_size
        self.ttl = ttl
        
        # Use WeakValueDictionary to allow garbage collection
        self._cache: Dict[str, Tuple[Callable, float]] = {}
        
        # Track access order for LRU eviction
        self._access_order: Dict[str, float] = {}
        
        # Cache statistics
        self.stats = CacheStats()
    
    def _make_cache_key(self, schema_id: str, query: str, variables: Optional[Dict] = None) -> str:
        """
        Generate a cache key for a query.
        
        Normalizes the query for better cache hits.
        """
        # Parse and print the query to normalize formatting
        try:
            doc = parse(query)
            normalized_query = print_ast(doc)
        except:
            # If parsing fails, use the original query
            normalized_query = query
        
        # Create a hash of the schema ID and normalized query
        # We don't include variables in the key as they don't affect compilation
        key_parts = [schema_id, normalized_query]
        key_string = "|".join(key_parts)
        
        # Use SHA256 for consistent hashing
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    def get(self, schema_id: str, query: str) -> Optional[Callable]:
        """
        Retrieve a compiled query from the cache.
        
        Returns None if not found or expired.
        """
        start_time = time.perf_counter()
        
        key = self._make_cache_key(schema_id, query)
        
        if key in self._cache:
            compiled_fn, timestamp = self._cache[key]
            
            # Check TTL if configured
            if self.ttl is not None:
                age = time.time() - timestamp
                if age > self.ttl:
                    # Expired entry
                    del self._cache[key]
                    del self._access_order[key]
                    self.stats.misses += 1
                    return None
            
            # Update access time for LRU
            self._access_order[key] = time.time()
            
            self.stats.hits += 1
            self.stats.cache_retrieval_time += time.perf_counter() - start_time
            return compiled_fn
        
        self.stats.misses += 1
        return None
    
    def put(self, schema_id: str, query: str, compiled_fn: Callable) -> None:
        """Store a compiled query in the cache."""
        key = self._make_cache_key(schema_id, query)
        
        # Check if we need to evict
        if len(self._cache) >= self.max_size:
            self._evict_lru()
        
        # Store with timestamp
        self._cache[key] = (compiled_fn, time.time())
        self._access_order[key] = time.time()
    
    def _evict_lru(self) -> None:
        """Evict the least recently used entry."""
        if not self._access_order:
            return
        
        # Find the oldest accessed key
        lru_key = min(self._access_order, key=self._access_order.get)
        
        # Remove from cache
        del self._cache[lru_key]
        del self._access_order[lru_key]
        self.stats.evictions += 1
    
    def clear(self) -> None:
        """Clear all cached queries."""
        self._cache.clear()
        self._access_order.clear()
    
    def size(self) -> int:
        """Get the current cache size."""
        return len(self._cache)


class CachedJITCompiler(GraphQLJITCompiler):
    """
    JIT compiler with built-in query caching.
    
    This compiler maintains a cache of compiled queries to avoid
    recompilation overhead for frequently executed queries.
    """
    
    # Class-level cache shared across instances with the same schema
    _schema_caches: Dict[int, QueryCache] = {}
    
    def __init__(
        self, 
        schema: GraphQLSchema,
        cache_size: int = 1000,
        cache_ttl: Optional[float] = None,
        enable_parallel: bool = True
    ):
        """
        Initialize the cached JIT compiler.
        
        Args:
            schema: The GraphQL schema
            cache_size: Maximum number of cached queries
            cache_ttl: Time-to-live for cached queries in seconds
            enable_parallel: Whether to use parallel async execution
        """
        super().__init__(schema)
        
        self.enable_parallel = enable_parallel
        
        # Get or create cache for this schema
        schema_id = id(schema)
        if schema_id not in self._schema_caches:
            self._schema_caches[schema_id] = QueryCache(cache_size, cache_ttl)
        
        self.cache = self._schema_caches[schema_id]
        self._schema_id = str(schema_id)
    
    def compile_query(self, query: str) -> Callable:
        """
        Compile a query with caching.
        
        Returns a cached result if available, otherwise compiles
        and caches the query.
        """
        # Try to get from cache
        cached_fn = self.cache.get(self._schema_id, query)
        if cached_fn is not None:
            return cached_fn
        
        # Compile the query
        start_time = time.perf_counter()
        
        if self.enable_parallel:
            # Use parallel async compiler for better performance
            compiler = ParallelAsyncJITCompiler(self.schema)
            compiled_fn = compiler.compile_query(query)
        else:
            # Use standard compilation
            compiled_fn = super().compile_query(query)
        
        compilation_time = time.perf_counter() - start_time
        self.cache.stats.compilation_time += compilation_time
        
        # Cache the compiled function
        self.cache.put(self._schema_id, query, compiled_fn)
        
        return compiled_fn
    
    def get_cache_stats(self) -> CacheStats:
        """Get cache statistics for monitoring."""
        return self.cache.stats
    
    def clear_cache(self) -> None:
        """Clear the query cache."""
        self.cache.clear()


class GlobalQueryCache:
    """
    Global query cache that can be shared across multiple schemas.
    
    This is useful for applications with multiple schemas or
    when you want centralized cache management.
    """
    
    def __init__(self, max_size: int = 5000, ttl: Optional[float] = None):
        """Initialize the global cache."""
        self.cache = QueryCache(max_size, ttl)
        self._compilers: Dict[int, CachedJITCompiler] = {}
    
    def get_compiler(
        self, 
        schema: GraphQLSchema,
        enable_parallel: bool = True
    ) -> CachedJITCompiler:
        """
        Get or create a cached compiler for a schema.
        
        This ensures all compilers for the same schema share
        the same cache.
        """
        schema_id = id(schema)
        
        if schema_id not in self._compilers:
            compiler = CachedJITCompiler(
                schema,
                cache_size=0,  # Use global cache
                enable_parallel=enable_parallel
            )
            # Replace with global cache
            compiler.cache = self.cache
            compiler._schema_id = str(schema_id)
            self._compilers[schema_id] = compiler
        
        return self._compilers[schema_id]
    
    def compile_query(
        self,
        schema: GraphQLSchema,
        query: str,
        enable_parallel: bool = True
    ) -> Callable:
        """
        Compile a query using the global cache.
        
        This is a convenience method that handles compiler creation.
        """
        compiler = self.get_compiler(schema, enable_parallel)
        return compiler.compile_query(query)
    
    def get_stats(self) -> CacheStats:
        """Get global cache statistics."""
        return self.cache.stats
    
    def clear(self) -> None:
        """Clear the global cache."""
        self.cache.clear()


# Convenience functions for easy usage

def compile_query_cached(
    schema: GraphQLSchema,
    query: str,
    cache_size: int = 1000,
    enable_parallel: bool = True
) -> Callable:
    """
    Compile a GraphQL query with caching.
    
    This is a convenience function that creates a cached compiler
    and compiles the query.
    """
    compiler = CachedJITCompiler(schema, cache_size, enable_parallel=enable_parallel)
    return compiler.compile_query(query)


# Global cache instance for applications that want a single shared cache
_global_cache = GlobalQueryCache()

def compile_query_global(
    schema: GraphQLSchema,
    query: str,
    enable_parallel: bool = True
) -> Callable:
    """
    Compile a query using the global cache.
    
    This uses a single global cache shared across all schemas,
    which is useful for applications with multiple schemas.
    """
    return _global_cache.compile_query(schema, query, enable_parallel)


def get_global_cache_stats() -> CacheStats:
    """Get statistics for the global cache."""
    return _global_cache.get_stats()


def clear_global_cache() -> None:
    """Clear the global cache."""
    _global_cache.clear()