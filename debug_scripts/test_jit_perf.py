"""Proper JIT performance test - compile once, execute many times."""

import asyncio
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "examples" / "jit-showcase"))

from graphql import execute, parse

from schema import Query, schema  # type: ignore
from strawberry.jit import compile_query

# Simple query for testing
QUERY = """
query TestQuery {
    posts(limit: 10) {
        id
        title
        content
        wordCount
        author {
            name
            email
            bio
            postsCount
        }
        comments(limit: 5) {
            id
            text
            likes
            author {
                name
            }
        }
    }
    featuredPost {
        id
        title
        viewCount
    }
}
"""


async def main():
    print("🔬 JIT Performance Test - Proper Measurement")
    print("=" * 70)

    root = Query()
    iterations = 100

    # Parse once for standard execution
    parsed_query = parse(QUERY)

    # Compile once for JIT
    print("Compiling query...")
    compile_start = time.perf_counter()
    compiled_fn = compile_query(schema, QUERY)
    compile_time = time.perf_counter() - compile_start
    print(f"✅ Compilation time: {compile_time * 1000:.2f}ms\n")

    # Warmup
    await execute(schema._schema, parsed_query, root_value=root)
    await compiled_fn(root)

    print(f"Running {iterations} iterations...\n")

    # Benchmark Standard GraphQL
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        await execute(schema._schema, parsed_query, root_value=root)
        times.append(time.perf_counter() - start)

    standard_avg = statistics.mean(times) * 1000  # Convert to ms
    standard_std = statistics.stdev(times) * 1000

    # Benchmark JIT
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        await compiled_fn(root)
        times.append(time.perf_counter() - start)

    jit_avg = statistics.mean(times) * 1000  # Convert to ms
    jit_std = statistics.stdev(times) * 1000

    # Results
    speedup = standard_avg / jit_avg
    improvement = ((standard_avg - jit_avg) / standard_avg) * 100

    print("📊 Results")
    print("=" * 70)
    print("Standard GraphQL:")
    print(f"  Average: {standard_avg:.3f}ms ± {standard_std:.3f}ms")
    print()
    print("JIT Compiled:")
    print(f"  Average: {jit_avg:.3f}ms ± {jit_std:.3f}ms")
    print()
    print(f"Speedup: {speedup:.2f}x")
    print(f"Improvement: {improvement:.1f}% faster")
    print()
    print("Throughput:")
    print(f"  Standard: {1000 / standard_avg:.1f} queries/sec")
    print(f"  JIT:      {1000 / jit_avg:.1f} queries/sec")
    print()

    if speedup > 1:
        print(f"✅ JIT is {speedup:.2f}x faster!")
    else:
        print(f"⚠️  JIT is {1 / speedup:.2f}x slower")
        print("   This needs investigation!")


if __name__ == "__main__":
    asyncio.run(main())
