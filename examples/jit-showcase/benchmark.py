"""Benchmark tool to compare standard GraphQL vs JIT compiled execution."""

import asyncio
import statistics
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from graphql import execute, parse

from schema import schema
from strawberry.jit import compile_query

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

    # 2. JIT Compiled (sequential)
    compiled_fn = compile_query(schema, query)
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        await compiled_fn(root)
        times.append(time.perf_counter() - start)

    avg_jit = statistics.mean(times)
    results["JIT Sequential"] = avg_jit
    speedup_jit = avg_standard / avg_jit

    # 3. JIT Compiled with Parallel Async
    compiled_parallel = compile_query(schema, query)
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        await compiled_parallel(root)
        times.append(time.perf_counter() - start)

    avg_parallel = statistics.mean(times)
    results["JIT Parallel"] = avg_parallel
    speedup_parallel = avg_standard / avg_parallel

    # 4. JIT with Caching (simulate multiple requests)
    # Simple query cache for demo

    query_cache = {}

    compiler = type(
        "QueryCache",
        (),
        {
            "compile_query": lambda self, q: query_cache.setdefault(
                q, compile_query(schema, q)
            )
        },
    )()

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
        speedup_cached = avg_standard / avg_cached

    return results


async def run_comprehensive_benchmark() -> None:
    """Run comprehensive benchmark across all query types."""
    all_results = {}

    print("\n📊 Comprehensive Benchmark Results")
    print("=" * 70)

    # Run benchmarks for each query type
    for query_name, query in QUERIES.items():
        results = await benchmark_query(query_name, query)
        all_results[query_name] = results

        print(f"\n🔍 Query: {query_name.upper()}")
        print("-" * 70)
        for method, avg_time in results.items():
            print(f"  {method:.<40} {avg_time * 1000:>10.2f}ms")

        # Calculate speedups for this query
        baseline = results["Standard GraphQL"]
        if "JIT Sequential" in results:
            speedup = baseline / results["JIT Sequential"]
            improvement = ((baseline - results["JIT Sequential"]) / baseline) * 100
            print(
                f"  JIT Sequential speedup: {speedup:.2f}x ({improvement:.1f}% faster)"
            )
        if "JIT Parallel" in results:
            speedup = baseline / results["JIT Parallel"]
            improvement = ((baseline - results["JIT Parallel"]) / baseline) * 100
            print(
                f"  JIT Parallel speedup:   {speedup:.2f}x ({improvement:.1f}% faster)"
            )
        if "JIT Cached" in results:
            speedup = baseline / results["JIT Cached"]
            improvement = ((baseline - results["JIT Cached"]) / baseline) * 100
            print(
                f"  JIT Cached speedup:     {speedup:.2f}x ({improvement:.1f}% faster)"
            )

    # Summary

    # Calculate average speedups
    speedups = {"JIT Sequential": [], "JIT Parallel": [], "JIT Cached": []}

    for query_name, results in all_results.items():
        baseline = results["Standard GraphQL"]
        for method in speedups:
            if method in results:
                speedups[method].append(baseline / results[method])

    print("\n🎯 Average Speedups Across All Queries")
    print("=" * 70)
    for method, values in speedups.items():
        if values:
            avg_speedup = statistics.mean(values)
            print(f"  {method:.<40} {avg_speedup:.2f}x faster")

    # Find best improvement
    max_speedup = 0
    best_query = ""
    for query_name, results in all_results.items():
        baseline = results["Standard GraphQL"]
        for method, time in results.items():
            if method != "Standard GraphQL":
                speedup = baseline / time
                if speedup > max_speedup:
                    max_speedup = speedup
                    best_query = f"{query_name} ({method})"

    print(f"\n⭐ Best improvement: {max_speedup:.2f}x on {best_query}")


async def simulate_production_load() -> None:
    """Simulate production-like query load."""
    from schema import Query

    root = Query()

    # Simulate query distribution (80/20 rule)
    # 80% of traffic is simple/medium queries
    # 20% is complex queries
    query_distribution = (
        ["simple"] * 40 + ["medium"] * 40 + ["complex"] * 15 + ["nested"] * 5
    )

    print("\n📊 Production Load Simulation")
    print("=" * 70)
    print(f"Total queries: {len(query_distribution)}")
    print(f"Distribution: simple={40}, medium={40}, complex={15}, nested={5}")

    # Standard execution
    start = time.perf_counter()
    for query_type in query_distribution:
        query = QUERIES[query_type]
        await execute(schema._schema, parse(query), root_value=root)
    standard_time = time.perf_counter() - start

    # JIT with caching (production setup)
    # Simple query cache for demo

    query_cache = {}

    compiler = type(
        "QueryCache",
        (),
        {
            "compile_query": lambda self, q: query_cache.setdefault(
                q, compile_query(schema, q)
            )
        },
    )()
    start = time.perf_counter()
    for query_type in query_distribution:
        query = QUERIES[query_type]
        compiled_fn = compiler.compile_query(query)
        await compiled_fn(root)
    jit_time = time.perf_counter() - start

    print("\n⏱️  Execution Times")
    print("-" * 70)
    standard_per_query = (standard_time / len(query_distribution)) * 1000
    jit_per_query = (jit_time / len(query_distribution)) * 1000

    print("Standard GraphQL:")
    print(f"  Total time: {standard_time * 1000:.2f}ms")
    print(f"  Per query:  {standard_per_query:.2f}ms")

    print("\nJIT with Cache:")
    print(f"  Total time: {jit_time * 1000:.2f}ms")
    print(f"  Per query:  {jit_per_query:.2f}ms")

    speedup = standard_time / jit_time
    improvement = ((standard_time - jit_time) / standard_time) * 100
    print(f"\nSpeedup:      {speedup:.2f}x faster")
    print(f"Improvement:  {improvement:.1f}%")
    print("Throughput (queries/sec):")
    print(f"  Standard: {len(query_distribution) / standard_time:.0f} q/s")
    print(f"  JIT:      {len(query_distribution) / jit_time:.0f} q/s")


async def main() -> None:
    """Main benchmark runner."""
    # Run comprehensive benchmark
    await run_comprehensive_benchmark()

    # Simulate production load
    await simulate_production_load()


if __name__ == "__main__":
    asyncio.run(main())
