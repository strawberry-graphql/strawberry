"""Test end-to-end: Strawberry schema → Rust execution
"""

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
    def hello(self) -> str:
        return "Hello from Python!"

    @strawberry.field
    def stadium(self, name: str = "Grand Stadium") -> Stadium:
        """Return a stadium with stands and seats."""
        # Create some sample seats
        seats = [
            Seat(x=i, y=j, labels=[f"Row-{j}", f"Seat-{i}", "Standard"])
            for j in range(3)
            for i in range(5)
        ]

        stands = [
            Stand(
                name="North Stand",
                seats=seats[:5],
                section_type="Standard",
                price_category="Bronze",
            ),
            Stand(
                name="South Stand",
                seats=seats[5:10],
                section_type="Standard",
                price_category="Bronze",
            ),
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

    print("=" * 80)
    print("TESTING RUST EXECUTION")
    print("=" * 80)
    print()

    # Test 1: Simple query
    print("Test 1: Simple hello query")
    query = "{ hello }"

    # Create root data that matches what our resolvers expect
    root_data = {
        "hello": "Hello from Rust!",
    }

    try:
        start = time.perf_counter()
        result = strawberry_core_rs.execute_query(sdl, query, root_data)
        elapsed = (time.perf_counter() - start) * 1000
        print(f"✅ Success ({elapsed:.2f}ms)")
        print(f"Result:\n{result}")
    except Exception as e:
        print(f"❌ Error: {e}")

    print()

    # Test 2: Stadium basic query
    print("Test 2: Stadium basic query")
    query = """
    {
        stadium(name: "Test Stadium") {
            name
            city
            country
        }
    }
    """

    # Create root data for stadium
    root_data = {
        "stadium": {
            "name": "Test Stadium",
            "city": "London",
            "country": "United Kingdom",
        }
    }

    try:
        start = time.perf_counter()
        result = strawberry_core_rs.execute_query(sdl, query, root_data)
        elapsed = (time.perf_counter() - start) * 1000
        print(f"✅ Success ({elapsed:.2f}ms)")
        print(f"Result:\n{result}")
    except Exception as e:
        print(f"❌ Error: {e}")

    print()
    print("=" * 80)
    print("COMPARISON: Python vs Rust Execution")
    print("=" * 80)
    print()

    # Compare with Python execution
    import asyncio

    async def test_python():
        print("Python execution:")
        query = "{ hello }"
        start = time.perf_counter()
        result = await schema.execute(query)
        elapsed = (time.perf_counter() - start) * 1000
        print(f"  Time: {elapsed:.2f}ms")
        if result.errors:
            print(f"  ❌ Errors: {result.errors}")
        else:
            print("  ✅ Success")

    asyncio.run(test_python())

    print()
    print("Rust execution:")
    query = "{ hello }"
    root_data = {"hello": "Hello from Rust!"}
    start = time.perf_counter()
    result = strawberry_core_rs.execute_query(sdl, query, root_data)
    elapsed = (time.perf_counter() - start) * 1000
    print(f"  Time: {elapsed:.2f}ms")
    print("  ✅ Success")


if __name__ == "__main__":
    main()
