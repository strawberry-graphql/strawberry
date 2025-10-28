"""Benchmark tool to compare standard GraphQL vs JIT compiled execution."""

import asyncio
import os
import statistics
import sys
import time

# Add parent directory to path for imports
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from graphql import execute, parse

from schema import schema

try:
    from strawberry.jit import CachedJITCompiler, compile_query

    JIT_AVAILABLE = True
except ImportError:
    JIT_AVAILABLE = False


# Test queries of varying complexity
QUERIES = {
    "simple": """
        query SimpleQuery {
            posts(limit: 5) {
                id
                title
            }
        }
    """,
    "medium": """
        query MediumQuery {
            posts(limit: 10) {
                id
                title
                content
                wordCount
                author {
                    name
                    email
                }
            }
            featuredPost {
                id
                title
                viewCount
            }
        }
    """,
    "complex": """
        query ComplexQuery {
            posts(limit: 10) {
                id
                title
                content
                wordCount
                viewCount
                author {
                    name
                    email
                    bio
                    postsCount
                    followers
                }
                comments(limit: 5) {
                    id
                    text
                    likes
                    isRecent
                    author {
                        name
                    }
                }
            }
            featuredPost {
                id
                title
                viewCount
                author {
                    name
                    postsCount
                }
            }
            topAuthors(limit: 5) {
                name
                bio
                postsCount
            }
        }
    """,
    "nested": """
        query DeeplyNested {
            posts(limit: 5) {
                id
                title
                author {
                    name
                    postsCount
                }
                comments(limit: 3) {
                    text
                    author {
                        name
                        followers
                    }
                }
                relatedPosts(limit: 2) {
                    id
                    title
                    author {
                        name
                    }
                    comments(limit: 2) {
                        text
                    }
                }
            }
        }
    """,
}


async def benchmark_query(query_name: str, query: str, iterations: int = 10):
    """Benchmark a single query with different execution methods."""
    # Create root object for execution
    from schema import Query

    root = Query()

    results = {}

    # 1. Standard GraphQL execution
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        await execute(schema._schema, parse(query), root_value=root)
        times.append(time.perf_counter() - start)

    avg_standard = statistics.mean(times)
    results["Standard GraphQL"] = avg_standard

    if not JIT_AVAILABLE:
        return results

    # 2. JIT Compiled (sequential)
    compiled_fn = compile_query(schema._schema, query)
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        await compiled_fn(root)
        times.append(time.perf_counter() - start)

    avg_jit = statistics.mean(times)
    results["JIT Sequential"] = avg_jit
    avg_standard / avg_jit

    # 3. JIT Compiled with Parallel Async
    compiled_parallel = compile_query(schema._schema, query)
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        await compiled_parallel(root)
        times.append(time.perf_counter() - start)

    avg_parallel = statistics.mean(times)
    results["JIT Parallel"] = avg_parallel
    avg_standard / avg_parallel

    # 4. JIT with Caching (simulate multiple requests)
    compiler = CachedJITCompiler(schema._schema, enable_parallel=True)

    # First execution (cache miss)
    start = time.perf_counter()
    compiled_cached = compiler.compile_query(query)
    await compiled_cached(root)
    time.perf_counter() - start

    # Subsequent executions (cache hits)
    times = []
    for _ in range(iterations - 1):
        start = time.perf_counter()
        compiled_cached = compiler.compile_query(query)
        await compiled_cached(root)
        times.append(time.perf_counter() - start)

    if times:
        avg_cached = statistics.mean(times)
        results["JIT Cached"] = avg_cached
        avg_standard / avg_cached

        compiler.get_cache_stats()

    return results


async def run_comprehensive_benchmark() -> None:
    """Run comprehensive benchmark across all query types."""
    all_results = {}

    # Run benchmarks for each query type
    for query_name, query in QUERIES.items():
        results = await benchmark_query(query_name, query)
        all_results[query_name] = results

    # Summary

    if JIT_AVAILABLE:
        # Calculate average speedups
        speedups = {"JIT Sequential": [], "JIT Parallel": [], "JIT Cached": []}

        for query_name, results in all_results.items():
            baseline = results["Standard GraphQL"]
            for method in speedups:
                if method in results:
                    speedups[method].append(baseline / results[method])

        for method, values in speedups.items():
            if values:
                statistics.mean(values)

        # Find best improvement
        max_speedup = 0
        for query_name, results in all_results.items():
            baseline = results["Standard GraphQL"]
            for method, time in results.items():
                if method != "Standard GraphQL":
                    speedup = baseline / time
                    max_speedup = max(max_speedup, speedup)


async def simulate_production_load() -> None:
    """Simulate production-like query load."""
    if not JIT_AVAILABLE:
        return

    from schema import Query

    root = Query()

    # Simulate query distribution (80/20 rule)
    # 80% of traffic is simple/medium queries
    # 20% is complex queries
    query_distribution = (
        ["simple"] * 40 + ["medium"] * 40 + ["complex"] * 15 + ["nested"] * 5
    )

    # Standard execution
    start = time.perf_counter()
    for query_type in query_distribution:
        query = QUERIES[query_type]
        await execute(schema._schema, parse(query), root_value=root)
    standard_time = time.perf_counter() - start

    # JIT with caching (production setup)
    compiler = CachedJITCompiler(schema._schema, enable_parallel=True)
    start = time.perf_counter()
    for query_type in query_distribution:
        query = QUERIES[query_type]
        compiled_fn = compiler.compile_query(query)
        await compiled_fn(root)
    jit_time = time.perf_counter() - start

    compiler.get_cache_stats()

    (standard_time / len(query_distribution)) * 1000
    (jit_time / len(query_distribution)) * 1000


async def main() -> None:
    """Main benchmark runner."""
    # Run comprehensive benchmark
    await run_comprehensive_benchmark()

    # Simulate production load
    await simulate_production_load()


if __name__ == "__main__":
    asyncio.run(main())
