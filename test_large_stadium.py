import time

import strawberry
from strawberry.extensions import Extension


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
