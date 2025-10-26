"""Test Rust execution with actual Python resolvers
"""


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
        print("[Python] hello() resolver called")
        return "Hello from Python resolver!"

    @strawberry.field
    def stadium(self, name: str = "Grand Stadium") -> Stadium:
        print(f"[Python] stadium() resolver called with name='{name}'")

        # Create some seats
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
    print("TEST: Rust calling Python resolvers")
    print("=" * 80)
    print()

    # Create a Query instance
    query_instance = Query()

    # Test 1: Simple hello
    print("Test 1: Simple hello query")
    print("-" * 40)
    query = "{ hello }"

    try:
        result = strawberry_core_rs.execute_query_with_resolvers(
            sdl, query, query_instance
        )
        print(f"Result:\n{result}")
    except Exception as e:
        print(f"❌ Error: {e}")

    print()

    # Test 2: Stadium basic
    print("Test 2: Stadium basic query")
    print("-" * 40)
    query = """
    {
        stadium(name: "Test Stadium") {
            name
            city
            country
        }
    }
    """

    try:
        result = strawberry_core_rs.execute_query_with_resolvers(
            sdl, query, query_instance
        )
        print(f"Result:\n{result}")
    except Exception as e:
        print(f"❌ Error: {e}")

    print()

    # Test 3: Stadium with stands (nested objects)
    print("Test 3: Stadium with stands")
    print("-" * 40)
    query = """
    {
        stadium {
            name
            stands {
                name
                sectionType
            }
        }
    }
    """

    try:
        result = strawberry_core_rs.execute_query_with_resolvers(
            sdl, query, query_instance
        )
        print(f"Result:\n{result}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
