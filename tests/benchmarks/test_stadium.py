"""Benchmark for a complex nested query with a large stadium dataset.

This benchmark tests Strawberry's performance when dealing with deeply nested
objects and large result sets. The stadium query generates approximately 50,000
seat objects across multiple stands, each with multiple labels and coordinates.
"""

import asyncio
from pathlib import Path
from typing import List

import pytest
from pytest_codspeed.plugin import BenchmarkFixture

import strawberry


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
    """Create a stadium with a configurable number of seats per row.

    Default configuration (250 seats/row) creates approximately 50,000 seats:
    - North Stand: 12,500 seats (50 rows × 250 seats)
    - South Stand: 12,500 seats (50 rows × 250 seats)
    - East Stand: 10,000 seats (40 rows × 250 seats)
    - West Stand: 10,000 seats (40 rows × 250 seats)
    """
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


@strawberry.type
class Query:
    @strawberry.field
    def stadium(self, seats_per_row: int) -> Stadium:
        return create_stadium(seats_per_row)


ROOT = Path(__file__).parent / "queries"
stadium_query = (ROOT / "stadium.graphql").read_text()


@pytest.mark.benchmark
@pytest.mark.parametrize(
    "seats_per_row", [250, 500], ids=lambda x: f"seats_per_row_{x}"
)
def test_stadium(benchmark: BenchmarkFixture, seats_per_row: int):
    """Benchmark a complex nested query with a large dataset.

    This test benchmarks the execution of a GraphQL query that returns
    a stadium with multiple stands, each containing thousands of seats.
    Each seat has multiple labels and coordinates.

    The benchmark tests with different seat counts:
    - 250 seats/row: ~45,000 total seats
    - 500 seats/row: ~90,000 total seats
    """
    schema = strawberry.Schema(query=Query)

    def run():
        return asyncio.run(
            schema.execute(
                stadium_query, variable_values={"seatsPerRow": seats_per_row}
            )
        )

    results = benchmark(run)

    assert results.errors is None
    assert results.data is not None
    assert results.data["stadium"]["name"] == "Grand Metropolitan Stadium"
