"""Test JIT with a simpler query to isolate the issue."""

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "examples" / "jit-showcase"))

from graphql import execute, parse

from schema import Query, schema  # type: ignore
from strawberry.jit import compile_query

# Very simple query with just one async field
SIMPLE_QUERY = """
query {
    posts(limit: 3) {
        id
        title
    }
}
"""


async def main():
    root = Query()
    parsed_query = parse(SIMPLE_QUERY)
    compiled_fn = compile_query(schema, SIMPLE_QUERY)

    iterations = 50

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

    print("Simple query (3 posts, 2 fields each):")
    print(f"  Standard: {std_avg:.2f}ms")
    print(f"  JIT:      {jit_avg:.2f}ms")
    print(f"  Ratio:    {jit_avg / std_avg:.2f}x")


if __name__ == "__main__":
    asyncio.run(main())
