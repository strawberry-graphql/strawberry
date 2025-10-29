"""Test JIT with progressive complexity to find the breaking point."""

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "examples" / "jit-showcase"))

from graphql import execute, parse

from schema import Query, schema  # type: ignore
from strawberry.jit import compile_query


async def benchmark_query(query_str, name):
    root = Query()
    parsed_query = parse(query_str)
    compiled_fn = compile_query(schema, query_str)

    iterations = 30

    # Warmup
    await execute(schema._schema, parsed_query, root_value=root)
    await compiled_fn(root)

    # Benchmark standard
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        await execute(schema._schema, parsed_query, root_value=root)
        times.append(time.perf_counter() - start)
    std_avg = sum(times) / len(times) * 1000

    # Benchmark JIT
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        await compiled_fn(root)
        times.append(time.perf_counter() - start)
    jit_avg = sum(times) / len(times) * 1000

    ratio = jit_avg / std_avg
    status = "✓" if ratio < 1.1 else "✗"
    print(
        f"{status} {name:40s} Standard: {std_avg:6.2f}ms  JIT: {jit_avg:6.2f}ms  Ratio: {ratio:.2f}x"
    )


async def main():
    print("\n🔬 Progressive Complexity Test\n")

    # Test 1: Simple query, no nesting
    await benchmark_query(
        """
        query {
            posts(limit: 3) {
                id
                title
            }
        }
        """,
        "Simple (3 posts, 2 sync fields)",
    )

    # Test 2: Add one async nested field
    await benchmark_query(
        """
        query {
            posts(limit: 3) {
                id
                title
                author {
                    name
                }
            }
        }
        """,
        "With author (1 async nested field)",
    )

    # Test 3: Add author's async field
    await benchmark_query(
        """
        query {
            posts(limit: 3) {
                id
                title
                author {
                    name
                    email
                    postsCount
                }
            }
        }
        """,
        "With author+postsCount (nested async)",
    )

    # Test 4: Add comments
    await benchmark_query(
        """
        query {
            posts(limit: 3) {
                id
                title
                author {
                    name
                    postsCount
                }
                comments(limit: 2) {
                    id
                    text
                }
            }
        }
        """,
        "With comments (2 per post)",
    )

    # Test 5: Add comment author (deeply nested)
    await benchmark_query(
        """
        query {
            posts(limit: 3) {
                id
                title
                author {
                    name
                    postsCount
                }
                comments(limit: 2) {
                    id
                    text
                    author {
                        name
                    }
                }
            }
        }
        """,
        "With comment authors (deeply nested)",
    )

    # Test 6: Increase scale
    await benchmark_query(
        """
        query {
            posts(limit: 10) {
                id
                title
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
        """,
        "Full query (10 posts, 5 comments each)",
    )

    print()


if __name__ == "__main__":
    asyncio.run(main())
