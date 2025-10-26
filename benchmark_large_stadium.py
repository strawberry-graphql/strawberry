"""Benchmark: Large Stadium (100,000 seats) - Python vs Rust
"""

import asyncio
import time

import strawberry_core_rs
from test_large_stadium import Query, schema

query = """
{
  stadium(seatsPerRow: 500) {
    city
    country
    name
    stands {
      sectionType
      seats {
        labels
        x
        y
      }
      priceCategory
      name
    }
  }
}
"""


def main():
    # Calculate expected data size
    # 4 stands: North (50 rows), South (50 rows), East (40 rows), West (40 rows)
    # = 180 total rows × 500 seats per row = 90,000 seats
    expected_seats = (50 + 50 + 40 + 40) * 500

    print("=" * 80)
    print("LARGE STADIUM BENCHMARK")
    print("=" * 80)
    print(f"Data size: ~{expected_seats:,} seats across 4 stands")
    print("Query: Full nested query with all fields")
    print()

    # Get the SDL
    sdl = str(schema)
    query_instance = Query()

    print("-" * 80)
    print("TEST 1: Python (Strawberry + graphql-core)")
    print("-" * 80)
    print()

    async def test_python():
        result = await schema.execute(query)
        if result.errors:
            print(f"❌ Errors: {result.errors}")
            return None
        return result.data

    # Run Python version
    start = time.perf_counter()
    result = asyncio.run(test_python())
    python_time = time.perf_counter() - start

    if result:
        # Count actual objects
        stands = result["stadium"]["stands"]
        total_seats = sum(len(stand["seats"]) for stand in stands)
        print(f"✅ Returned {len(stands)} stands with {total_seats:,} total seats")
        print(f"⏱️  Total time: {python_time:.3f}s ({python_time * 1000:.1f}ms)")

    print()
    print("-" * 80)
    print("TEST 2: Rust (apollo-compiler + PyO3 + Python resolvers)")
    print("-" * 80)
    print()

    # Run Rust version
    start = time.perf_counter()
    try:
        result_json = strawberry_core_rs.execute_query_with_resolvers(
            sdl, query, query_instance
        )
        rust_time = time.perf_counter() - start

        # Parse result to count objects
        import json

        result = json.loads(result_json)

        if result.get("errors"):
            print(f"❌ Errors: {result['errors']}")
        elif result.get("data"):
            stands = result["data"]["stadium"]["stands"]
            total_seats = sum(len(stand["seats"]) for stand in stands)
            print(f"✅ Returned {len(stands)} stands with {total_seats:,} total seats")
            print(f"⏱️  Total time: {rust_time:.3f}s ({rust_time * 1000:.1f}ms)")
        else:
            print("❌ Unexpected result format")
            rust_time = None
    except Exception as e:
        print(f"❌ Error: {e}")
        rust_time = None

    print()
    print("=" * 80)
    print("RESULTS COMPARISON")
    print("=" * 80)
    print()

    if rust_time:
        print(f"Python time:  {python_time:.3f}s ({python_time * 1000:.1f}ms)")
        print(f"Rust time:    {rust_time:.3f}s ({rust_time * 1000:.1f}ms)")
        print()

        if rust_time < python_time:
            speedup = python_time / rust_time
            saved = python_time - rust_time
            print(f"🚀 Rust is {speedup:.2f}x FASTER!")
            print(f"   Time saved: {saved:.3f}s ({saved * 1000:.1f}ms)")
            print(
                f"   Improvement: {((python_time - rust_time) / python_time * 100):.1f}%"
            )
        else:
            slowdown = rust_time / python_time
            print(f"⚠️  Rust is {slowdown:.2f}x slower")
    else:
        print(f"Python time:  {python_time:.3f}s ({python_time * 1000:.1f}ms)")
        print("Rust time:    N/A (error occurred)")

    print()
    print("=" * 80)
    print("DATA SIZE ANALYSIS")
    print("=" * 80)
    print()
    print(f"Total objects processed: ~{expected_seats:,} seats + 4 stands + 1 stadium")
    print(f"                       = ~{expected_seats + 5:,} total objects")
    print()
    print("This represents a realistic large query that might occur in production!")
    print()


if __name__ == "__main__":
    main()
