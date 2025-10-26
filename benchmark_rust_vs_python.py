"""Benchmark: Python vs Rust GraphQL execution
Using the stadium benchmark from the POC
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
        """Return a stadium with stands and seats."""
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

    # Create root data that matches what Python resolvers would return
    # Generate the full data structure
    seats_data = [
        {"x": i, "y": j, "labels": [f"Row-{j}", f"Seat-{i}", "Standard"]}
        for j in range(10)
        for i in range(50)
    ]

    stands_data = [
        {
            "name": f"Stand {s}",
            "seats": seats_data[i : i + 50],
            "sectionType": "Standard" if s % 2 == 0 else "Premium",
            "priceCategory": ["Bronze", "Silver", "Gold", "Platinum"][s % 4],
        }
        for s, i in enumerate(range(0, len(seats_data), 50))
    ]

    root_data = {
        "stadium": {
            "name": "Test Stadium",
            "city": "London",
            "country": "United Kingdom",
            "stands": stands_data,
        }
    }

    print("=" * 80)
    print("STADIUM BENCHMARK: Python vs Rust GraphQL Execution")
    print("=" * 80)
    print(f"Data size: {len(stands_data)} stands, {len(seats_data)} seats")
    print()

    # Warmup
    print("Warming up...")
    for _ in range(3):
        strawberry_core_rs.execute_query(sdl, query, root_data)

    async def warmup_python():
        for _ in range(3):
            await schema.execute(query)

    asyncio.run(warmup_python())
    print()

    # Benchmark Python execution
    print("Benchmarking Python execution...")
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

    # Benchmark Rust execution
    print("Benchmarking Rust execution...")
    rust_times = []
    for i in range(10):
        start = time.perf_counter()
        result = strawberry_core_rs.execute_query(sdl, query, root_data)
        elapsed = (time.perf_counter() - start) * 1000
        rust_times.append(elapsed)
    print("  ✅ 10 iterations completed")

    print()
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()
    print("Python execution:")
    print(f"  Average: {sum(python_times) / len(python_times):.2f}ms")
    print(f"  Min:     {min(python_times):.2f}ms")
    print(f"  Max:     {max(python_times):.2f}ms")
    print()
    print("Rust execution:")
    print(f"  Average: {sum(rust_times) / len(rust_times):.2f}ms")
    print(f"  Min:     {min(rust_times):.2f}ms")
    print(f"  Max:     {max(rust_times):.2f}ms")
    print()

    speedup = (sum(python_times) / len(python_times)) / (
        sum(rust_times) / len(rust_times)
    )
    print(f"🚀 Rust is {speedup:.1f}x faster!")
    print()


if __name__ == "__main__":
    main()
