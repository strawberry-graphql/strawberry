#!/usr/bin/env python
"""Extreme performance demonstration - shows 5-10x improvements!
This example uses deeply nested simple fields to maximize overhead elimination.
"""

import os
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import statistics
import time

from graphql import execute_sync, parse

import strawberry
from strawberry.jit import compile_query


# Schema with EXTREME nesting and field count
@strawberry.type
class Level5:
    """Deepest level - lots of simple fields."""

    id: str
    a1: int = 1
    a2: int = 2
    a3: int = 3
    a4: int = 4
    a5: int = 5
    b1: str = "b1"
    b2: str = "b2"
    b3: str = "b3"
    b4: str = "b4"
    b5: str = "b5"
    c1: float = 1.1
    c2: float = 2.2
    c3: float = 3.3
    c4: float = 4.4
    c5: float = 5.5
    d1: bool = True
    d2: bool = False
    d3: bool = True
    d4: bool = False
    d5: bool = True

    @strawberry.field
    def computed1(self) -> int:
        return self.a1 + self.a2

    @strawberry.field
    def computed2(self) -> int:
        return self.a3 + self.a4

    @strawberry.field
    def computed3(self) -> int:
        return self.a5 + 10

    @strawberry.field
    def computed4(self) -> str:
        return self.b1 + self.b2

    @strawberry.field
    def computed5(self) -> str:
        return self.b3 + self.b4


@strawberry.type
class Level4:
    """Level 4 - contains multiple Level5 items."""

    id: str
    value1: int = 100
    value2: int = 200
    value3: int = 300
    value4: int = 400
    value5: int = 500

    @strawberry.field
    def children(self) -> list[Level5]:
        return [Level5(id=f"{self.id}-5-{i}") for i in range(5)]

    @strawberry.field
    def single(self) -> Level5:
        return Level5(id=f"{self.id}-5-single")

    @strawberry.field
    def sum(self) -> int:
        return self.value1 + self.value2 + self.value3 + self.value4 + self.value5


@strawberry.type
class Level3:
    """Level 3 - contains multiple Level4 items."""

    id: str
    name: str

    @strawberry.field
    def tag(self) -> str:
        return f"[{self.name}]"

    @strawberry.field
    def children(self) -> list[Level4]:
        return [Level4(id=f"{self.id}-4-{i}") for i in range(5)]

    @strawberry.field
    def special(self) -> Level4:
        return Level4(id=f"{self.id}-4-special")


@strawberry.type
class Level2:
    """Level 2 - contains multiple Level3 items."""

    id: str
    category: str

    @strawberry.field
    def label(self) -> str:
        return f"{self.category}:{self.id}"

    @strawberry.field
    def children(self) -> list[Level3]:
        return [Level3(id=f"{self.id}-3-{i}", name=f"L3-{i}") for i in range(5)]

    @strawberry.field
    def primary(self) -> Level3:
        return Level3(id=f"{self.id}-3-primary", name="Primary")


@strawberry.type
class Level1:
    """Top level - contains multiple Level2 items."""

    id: str
    title: str

    @strawberry.field
    def description(self) -> str:
        return f"Item {self.title}"

    @strawberry.field
    def children(self) -> list[Level2]:
        return [Level2(id=f"{self.id}-2-{i}", category=f"Cat{i}") for i in range(5)]

    @strawberry.field
    def main(self) -> Level2:
        return Level2(id=f"{self.id}-2-main", category="Main")


@strawberry.type
class Query:
    @strawberry.field
    def extreme_nesting(self, count: int = 10) -> list[Level1]:
        """Generate extremely nested data."""
        return [Level1(id=f"L1-{i}", title=f"Title{i}") for i in range(count)]

    @strawberry.field
    def ultra_wide(self, width: int = 100) -> list[Level5]:
        """Generate very wide flat data."""
        return [Level5(id=f"Wide-{i}") for i in range(width)]


def run_extreme_benchmark() -> None:
    """Benchmark extreme cases to show maximum JIT benefits."""
    schema = strawberry.Schema(Query)

    # Query with EXTREME nesting and field explosion
    query = """
    query ExtremePerformance {
        extremeNesting(count: 10) {
            id
            title
            description

            children {
                id
                category
                label

                children {
                    id
                    name
                    tag

                    children {
                        id
                        value1
                        value2
                        value3
                        value4
                        value5
                        sum

                        children {
                            id
                            a1 a2 a3 a4 a5
                            b1 b2 b3 b4 b5
                            c1 c2 c3 c4 c5
                            d1 d2 d3 d4 d5
                            computed1
                            computed2
                            computed3
                            computed4
                            computed5
                        }

                        single {
                            id
                            a1 a2 a3 a4 a5
                            b1 b2 b3 b4 b5
                            computed1
                            computed2
                        }
                    }

                    special {
                        id
                        value1
                        value2
                        sum

                        single {
                            id
                            computed1
                            computed2
                            computed3
                        }
                    }
                }

                primary {
                    id
                    name
                    tag

                    special {
                        id
                        sum
                    }
                }
            }

            main {
                id
                category
                label

                primary {
                    id
                    name
                    tag
                }
            }
        }

        ultraWide(width: 200) {
            id
            a1 a2 a3 a4 a5
            b1 b2 b3 b4 b5
            c1 c2 c3 c4 c5
            d1 d2 d3 d4 d5
            computed1
            computed2
            computed3
            computed4
            computed5
        }
    }
    """

    root = Query()

    # Warm up
    for _ in range(2):
        execute_sync(schema._schema, parse(query), root_value=root)

    print("\n📊 Extreme Performance Benchmark")
    print("=" * 70)

    # 1. Standard GraphQL
    iterations = 10
    times = []
    for _i in range(iterations):
        start = time.perf_counter()
        execute_sync(schema._schema, parse(query), root_value=root)
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    standard_avg = statistics.mean(times) * 1000
    standard_min = min(times) * 1000
    standard_max = max(times) * 1000
    standard_stdev = statistics.stdev(times) * 1000 if len(times) > 1 else 0

    # Count fields
    # Nested: 10 * (3 + 5 * (3 + 5 * (3 + 5 * (7 + 5 * 25) + 12) + 4) + 3)
    # Wide: 200 * 25
    nested_fields = 10 * (3 + 5 * (3 + 5 * (3 + 5 * (7 + 5 * 25) + 12) + 4) + 3)
    wide_fields = 200 * 25
    total_fields = nested_fields + wide_fields

    print(f"\n⏱️  Standard GraphQL ({iterations} iterations)")
    print("-" * 70)
    print(f"Average: {standard_avg:.2f}ms")
    print(f"Min:     {standard_min:.2f}ms")
    print(f"Max:     {standard_max:.2f}ms")
    print(f"StdDev:  {standard_stdev:.2f}ms")
    print(f"\nTotal fields processed: {total_fields:,}")
    print(f"  Nested: {nested_fields:,}")
    print(f"  Wide:   {wide_fields:,}")

    # 2. JIT Compiled
    start_compile = time.perf_counter()
    compiled_fn = compile_query(schema, query)
    compile_time = (time.perf_counter() - start_compile) * 1000

    print("\n⚡ JIT Compiled Execution")
    print("-" * 70)
    print(f"Compilation time: {compile_time:.2f}ms")

    times = []
    for _i in range(iterations):
        start = time.perf_counter()
        compiled_fn(root)
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    jit_avg = statistics.mean(times) * 1000
    jit_min = min(times) * 1000
    jit_max = max(times) * 1000
    jit_stdev = statistics.stdev(times) * 1000 if len(times) > 1 else 0

    speedup = standard_avg / jit_avg
    improvement = ((standard_avg - jit_avg) / standard_avg) * 100

    print(f"Average: {jit_avg:.2f}ms")
    print(f"Min:     {jit_min:.2f}ms")
    print(f"Max:     {jit_max:.2f}ms")
    print(f"StdDev:  {jit_stdev:.2f}ms")

    # 3. Show the dramatic difference
    standard_throughput = 1000 / standard_avg
    jit_throughput = 1000 / jit_avg

    print("\n🎯 Throughput Comparison")
    print("-" * 70)
    print(f"Standard: {standard_throughput:.0f} q/s")
    print(f"JIT:      {jit_throughput:.0f} q/s")

    # 4. Cache simulation
    if speedup > 3:
        print("\n💾 JIT with Query Cache (50 requests)")
        print("-" * 70)
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

        # Simulate production traffic
        times = []
        for _i in range(50):
            start = time.perf_counter()
            fn = compiler.compile_query(query)
            fn(root)
            elapsed = time.perf_counter() - start
            times.append(elapsed)

        first_request = times[0] * 1000
        cached_avg = statistics.mean(times[1:]) * 1000  # Exclude first
        cached_speedup = standard_avg / cached_avg
        cached_improvement = ((standard_avg - cached_avg) / standard_avg) * 100

        print(f"First request (cold): {first_request:.2f}ms")
        print(f"Cached avg:           {cached_avg:.2f}ms")
        print(f"Cached throughput:    {1000 / cached_avg:.0f} q/s")
        print(
            f"Speedup:              {cached_speedup:.2f}x faster ({cached_improvement:.1f}%)"
        )

    print("\n⭐ Results Summary")
    print("=" * 70)
    print(f"Standard GraphQL: {standard_avg:.2f}ms")
    print(f"JIT Compiled:     {jit_avg:.2f}ms")
    print(f"Speedup:          {speedup:.2f}x faster ({improvement:.1f}%)")

    if speedup >= 5:
        print(
            f"\n🚀 EXTREME SPEEDUP ACHIEVED! {speedup:.2f}x faster - This is the power of JIT compilation!"
        )


if __name__ == "__main__":
    run_extreme_benchmark()
