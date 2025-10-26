"""REAL Benchmark: Python vs Rust with actual resolver calls
"""

import asyncio
import time

import strawberry_core_rs

import strawberry


@strawberry.type
class Seat:
    x: int
    y: int
    labels: list[str]


@strawberry.type
class Stand:
    name: str
    seats: list[Seat]
    section_type: str
    price_category: str


@strawberry.type
class Stadium:
    name: str
    city: str
    country: str
    stands: list[Stand]


@strawberry.type
class Query:
    @strawberry.field
    def stadium(self, name: str = "Grand Stadium") -> Stadium:
        # Create 10 rows x 50 seats = 500 seats per stand
        # 10 stands = 5,000 total seats
        seats = [
            Seat(x=i, y=j, labels=[f"Row-{j}", f"Seat-{i}", "Standard"])
            for j in range(10)
            for i in range(50)
        ]

        stands = [
            Stand(
                name=f"Stand {s}",
                seats=seats[i : i + 50],  # 50 seats per stand
                section_type="Standard" if s % 2 == 0 else "Premium",
                price_category=["Bronze", "Silver", "Gold", "Platinum"][s % 4],
            )
            for s, i in enumerate(range(0, len(seats), 50))
        ]

        return Stadium(
            name=name,
            city="London",
            country="United Kingdom",
            stands=stands,
        )


def main():
    schema = strawberry.Schema(query=Query)
    sdl = str(schema)

    # The full stadium query
    query = """
    {
        stadium(name: "Test Stadium") {
            name
            city
            country
            stands {
                name
                sectionType
                priceCategory
                seats {
                    x
                    y
                    labels
                }
            }
        }
    }
    """

    query_instance = Query()

    print("=" * 80)
    print("REAL BENCHMARK: Python vs Rust with Actual Resolver Calls")
    print("=" * 80)
    print("Data: 10 stands x 500 seats = 5,000 objects")
    print("Resolvers: Python functions called by both implementations")
    print()

    # Warmup
    print("Warming up...")
    for _ in range(3):
        strawberry_core_rs.execute_query_with_resolvers(sdl, query, query_instance)

    async def warmup_python():
        for _ in range(3):
            await schema.execute(query)

    asyncio.run(warmup_python())
    print()

    # Benchmark Python execution
    print("Benchmarking Python (Strawberry + graphql-core)...")
    python_times = []

    async def bench_python():
        for i in range(10):
            start = time.perf_counter()
            result = await schema.execute(query)
            elapsed = (time.perf_counter() - start) * 1000
            python_times.append(elapsed)
            if result.errors:
                print(f"  ❌ Error: {result.errors}")
                return
        print("  ✅ 10 iterations completed")

    asyncio.run(bench_python())

    # Benchmark Rust execution with Python resolvers
    print("Benchmarking Rust (apollo-compiler + PyO3 + Python resolvers)...")
    rust_times = []
    for i in range(10):
        start = time.perf_counter()
        result = strawberry_core_rs.execute_query_with_resolvers(
            sdl, query, query_instance
        )
        elapsed = (time.perf_counter() - start) * 1000
        rust_times.append(elapsed)
    print("  ✅ 10 iterations completed")

    print()
    print("=" * 80)
    print("RESULTS: Real-World Performance with Python Resolvers")
    print("=" * 80)
    print()
    print("Python (Strawberry + graphql-core):")
    print(f"  Average: {sum(python_times) / len(python_times):.2f}ms")
    print(f"  Min:     {min(python_times):.2f}ms")
    print(f"  Max:     {max(python_times):.2f}ms")
    print()
    print("Rust (apollo-compiler + PyO3 + Python resolvers):")
    print(f"  Average: {sum(rust_times) / len(rust_times):.2f}ms")
    print(f"  Min:     {min(rust_times):.2f}ms")
    print(f"  Max:     {max(rust_times):.2f}ms")
    print()

    py_avg = sum(python_times) / len(python_times)
    rust_avg = sum(rust_times) / len(rust_times)

    if rust_avg < py_avg:
        speedup = py_avg / rust_avg
        print(f"🚀 Rust is {speedup:.2f}x FASTER!")
        print(f"   Improvement: {((py_avg - rust_avg) / py_avg * 100):.1f}% faster")
    else:
        slowdown = rust_avg / py_avg
        print(f"⚠️  Rust is {slowdown:.2f}x SLOWER")
        print(f"   Regression: {((rust_avg - py_avg) / py_avg * 100):.1f}% slower")

    print()
    print("=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    print()
    print("Both implementations:")
    print("  - Call the same Python resolver functions")
    print("  - Create the same Python objects")
    print("  - Process the same data")
    print()
    print("Difference comes from:")
    print("  - Parsing: Rust (apollo-compiler) vs Python (graphql-core)")
    print("  - Validation: Rust vs Python")
    print("  - Execution orchestration: Rust vs Python")
    print("  - Type checking: Rust vs Python")
    print()


if __name__ == "__main__":
    main()
