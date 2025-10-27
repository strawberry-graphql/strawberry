"""Test the stadium benchmark with JIT compiler."""

import time
from typing import List

import strawberry
from strawberry.extensions import Extension
from strawberry.jit import compile_query


@strawberry.type
class Seat:
    x: int
    y: int
    labels: List[str]


@strawberry.type
class Stand:
    name: str
    seats: List[Seat]
    section_type: str
    price_category: str


@strawberry.type
class Stadium:
    name: str
    city: str
    country: str
    stands: List[Stand]


def generate_seats_for_stand(
    stand_name: str,
    rows: int,
    seats_per_row: int,
    x_offset: int,
    y_offset: int,
    section_type: str,
) -> List[Seat]:
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

    # North Stand - 12,500 seats
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

    # South Stand - 12,500 seats
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

    # East Stand - 10,000 seats (Premium)
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

    # West Stand - 10,000 seats (Premium)
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


class ResponseTimeLoggingExtension(Extension):
    def on_request_start(self):
        self.start_time = time.perf_counter()

    def on_request_end(self):
        end_time = time.perf_counter()
        execution_time = end_time - self.start_time
        print(f"[Response Time] Query executed in {execution_time:.2f}s")

    def on_execute(self):
        self.execute_start = time.perf_counter()
        yield
        execute_time = time.perf_counter() - self.execute_start
        print(f"[Execute Time] Resolver execution took {execute_time:.2f}s")


@strawberry.type
class Query:
    @strawberry.field
    def stadium(self, seats_per_row: int) -> Stadium:
        _time = time.perf_counter()
        stadium = create_stadium(seats_per_row)
        print(
            f"[Building Time] Took {time.perf_counter() - _time:.2f}s to construct stadium"
        )
        return stadium


# Create the Strawberry schema with the extension
schema = strawberry.Schema(query=Query, extensions=[ResponseTimeLoggingExtension])

# The query from the user
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


def test_stadium_standard_execution():
    """Test stadium with standard GraphQL execution."""
    print("\n" + "=" * 80)
    print("STANDARD EXECUTION")
    print("=" * 80)

    from graphql import execute_sync, parse

    start = time.perf_counter()
    result = execute_sync(schema._schema, parse(query))
    duration = time.perf_counter() - start

    print(f"Standard execution took: {duration:.2f}s")

    # Verify result
    assert result.data is not None, "Result data is None"
    assert "stadium" in result.data, "Stadium not in result"
    stadium = result.data["stadium"]
    assert stadium["name"] == "Grand Metropolitan Stadium"
    assert len(stadium["stands"]) == 4

    # Count seats
    total_seats = sum(len(stand["seats"]) for stand in stadium["stands"])
    print(f"Total seats in result: {total_seats:,}")

    # Verify seat structure
    first_seat = stadium["stands"][0]["seats"][0]
    assert "x" in first_seat
    assert "y" in first_seat
    assert "labels" in first_seat
    assert len(first_seat["labels"]) == 5

    return result, duration


def test_stadium_jit_execution():
    """Test stadium with JIT compiled execution."""
    print("\n" + "=" * 80)
    print("JIT EXECUTION")
    print("=" * 80)

    # Compile the query
    print("Compiling query...")
    compile_start = time.perf_counter()
    compiled_fn = compile_query(schema, query)
    compile_time = time.perf_counter() - compile_start
    print(f"Compilation took: {compile_time:.4f}s")

    # Execute
    print("\nExecuting compiled query...")
    exec_start = time.perf_counter()
    result = compiled_fn(None)
    exec_time = time.perf_counter() - exec_start

    print(f"JIT execution took: {exec_time:.2f}s")

    # Handle both dict result and direct data
    if isinstance(result, dict) and "data" in result:
        data = result["data"]
        errors = result.get("errors", [])
    else:
        data = result
        errors = []

    # Check for errors
    if errors:
        print(f"\n⚠️  ERRORS FOUND ({len(errors)}):")
        for i, err in enumerate(errors[:5], 1):  # Show first 5 errors
            print(f"  {i}. {err.get('message', err)}")
            print(f"     Path: {err.get('path', [])}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more errors")

    # Verify result
    assert data is not None, "Result data is None"
    assert "stadium" in data, "Stadium not in result"
    stadium = data["stadium"]
    assert stadium["name"] == "Grand Metropolitan Stadium", (
        f"Wrong stadium name: {stadium.get('name')}"
    )
    assert len(stadium["stands"]) == 4, (
        f"Wrong number of stands: {len(stadium.get('stands', []))}"
    )

    # Count seats
    total_seats = sum(len(stand["seats"]) for stand in stadium["stands"])
    print(f"Total seats in result: {total_seats:,}")

    # Verify seat structure
    first_seat = stadium["stands"][0]["seats"][0]
    assert "x" in first_seat, "Seat missing x coordinate"
    assert "y" in first_seat, "Seat missing y coordinate"
    assert "labels" in first_seat, "Seat missing labels"
    assert len(first_seat["labels"]) == 5, (
        f"Wrong number of labels: {len(first_seat.get('labels', []))}"
    )

    return result, exec_time


def test_compare_results():
    """Compare standard and JIT execution results."""
    print("\n" + "=" * 80)
    print("COMPARISON")
    print("=" * 80)

    std_result, std_time = test_stadium_standard_execution()
    jit_result, jit_time = test_stadium_jit_execution()

    print("\n" + "-" * 80)
    print("RESULTS:")
    print("-" * 80)
    print(f"Standard execution: {std_time:.2f}s")
    print(f"JIT execution:      {jit_time:.2f}s")

    speedup = std_time / jit_time if jit_time > 0 else 0
    print(f"Speedup:            {speedup:.2f}x")

    if speedup > 1:
        print(f"\n✅ JIT is {speedup:.2f}x FASTER")
    elif speedup < 1:
        print(f"\n⚠️  JIT is {1 / speedup:.2f}x SLOWER")
    else:
        print("\n➖ Same performance")

    # Compare data equality
    std_data = std_result.data
    jit_data = jit_result.get("data") if isinstance(jit_result, dict) else jit_result

    if std_data == jit_data:
        print("✅ Results are IDENTICAL")
    else:
        print("❌ Results DIFFER")
        print(f"\nStandard keys: {list(std_data.keys()) if std_data else None}")
        print(f"JIT keys:      {list(jit_data.keys()) if jit_data else None}")


if __name__ == "__main__":
    try:
        test_compare_results()
        print("\n" + "=" * 80)
        print("✅ STADIUM BENCHMARK PASSED")
        print("=" * 80)
    except AssertionError as e:
        print("\n" + "=" * 80)
        print("❌ STADIUM BENCHMARK FAILED")
        print("=" * 80)
        print(f"Error: {e}")
        raise
    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ STADIUM BENCHMARK CRASHED")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        raise
