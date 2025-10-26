"""Benchmark: Large Stadium (100,000 seats) - Python vs Rust
Modified to work without argument passing (for now)
"""

import asyncio
import time

import strawberry_core_rs

import strawberry


# Copy all the types and functions from test_large_stadium
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


def generate_seats_for_stand(
    stand_name: str,
    rows: int,
    seats_per_row: int,
    x_offset: int,
    y_offset: int,
    section_type: str,
) -> list[Seat]:
    """Generate seats for a stand with proper coordinates and labels."""
    seats = []

    for row in range(rows):
        for seat_num in range(seats_per_row):
            x = x_offset + seat_num
            y = y_offset + row

            row_label = (
                chr(65 + row)
                if row < 26
                else f"{chr(65 + row // 26)}{chr(65 + row % 26)}"
            )

            labels = [
                stand_name,
                f"Row-{row_label}",
                f"Seat-{seat_num + 1}",
                section_type,
                f"Block-{(row // 5) + 1}",
            ]

            seats.append(Seat(x=x, y=y, labels=labels))

    return seats


def create_stadium(seats_per_row: int = 250) -> Stadium:
    """Create a stadium with approximately 50,000 seats."""
    stands = []

    # North Stand
    north_stand_seats = generate_seats_for_stand(
        stand_name="North-Stand",
        rows=50,
        seats_per_row=seats_per_row,
        x_offset=0,
        y_offset=0,
        section_type="Standard",
    )
    stands.append(
        Stand(
            name="North Stand",
            seats=north_stand_seats,
            section_type="Standard",
            price_category="Bronze",
        )
    )

    # South Stand
    south_stand_seats = generate_seats_for_stand(
        stand_name="South-Stand",
        rows=50,
        seats_per_row=seats_per_row,
        x_offset=0,
        y_offset=100,
        section_type="Standard",
    )
    stands.append(
        Stand(
            name="South Stand",
            seats=south_stand_seats,
            section_type="Standard",
            price_category="Bronze",
        )
    )

    # East Stand
    east_stand_seats = generate_seats_for_stand(
        stand_name="East-Stand",
        rows=40,
        seats_per_row=seats_per_row,
        x_offset=300,
        y_offset=20,
        section_type="Premium",
    )
    stands.append(
        Stand(
            name="East Stand",
            seats=east_stand_seats,
            section_type="Premium",
            price_category="Gold",
        )
    )

    # West Stand
    west_stand_seats = generate_seats_for_stand(
        stand_name="West-Stand",
        rows=40,
        seats_per_row=seats_per_row,
        x_offset=-300,
        y_offset=20,
        section_type="Premium",
    )
    stands.append(
        Stand(
            name="West Stand",
            seats=west_stand_seats,
            section_type="Premium",
            price_category="Gold",
        )
    )

    return Stadium(
        name="Grand Metropolitan Stadium",
        city="London",
        country="United Kingdom",
        stands=stands,
    )


# Modified Query - hardcode seats_per_row for now
@strawberry.type
class Query:
    @strawberry.field
    def stadium(self) -> Stadium:
        # Hardcode 500 seats per row for this benchmark
        _time = time.perf_counter()
        stadium = create_stadium(seats_per_row=500)
        build_time = time.perf_counter() - _time
        print(f"[Building Time] Took {build_time:.2f}s to construct stadium")
        return stadium


schema = strawberry.Schema(query=Query)

# Simplified query without arguments
query = """
{
  stadium {
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
    expected_seats = (50 + 50 + 40 + 40) * 500

    print("=" * 80)
    print("LARGE STADIUM BENCHMARK")
    print("=" * 80)
    print(f"Data size: ~{expected_seats:,} seats across 4 stands")
    print("Query: Full nested query with all fields")
    print()

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
            return None, 0
        return result.data, 0

    start = time.perf_counter()
    result, _ = asyncio.run(test_python())
    python_time = time.perf_counter() - start

    if result:
        stands = result["stadium"]["stands"]
        total_seats = sum(len(stand["seats"]) for stand in stands)
        print(f"✅ Returned {len(stands)} stands with {total_seats:,} total seats")
        print(f"⏱️  Total time: {python_time:.3f}s ({python_time * 1000:.1f}ms)")

    print()
    print("-" * 80)
    print("TEST 2: Rust (apollo-compiler + PyO3 + Python resolvers)")
    print("-" * 80)
    print()

    start = time.perf_counter()
    try:
        result_json = strawberry_core_rs.execute_query_with_resolvers(
            sdl, query, query_instance
        )
        rust_time = time.perf_counter() - start

        import json

        result = json.loads(result_json)

        if result.get("errors"):
            print(f"❌ Errors: {result['errors']}")
            rust_time = None
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
        import traceback

        traceback.print_exc()
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
    print("NOTE: Argument passing not yet implemented")
    print("=" * 80)
    print()
    print("The `seatsPerRow` argument was hardcoded to 500 in the resolver")
    print("to work around the missing argument extraction feature.")
    print()


if __name__ == "__main__":
    main()
