"""Test Strawberry schema execution with Rust.

This creates a real Strawberry schema and attempts to execute it using
the apollo-compiler Rust execution engine.
"""


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
    """Generate SDL and test data for Rust execution."""
    schema = strawberry.Schema(query=Query)

    # Get SDL representation
    sdl = str(schema)
    print("=" * 80)
    print("STRAWBERRY SCHEMA (SDL)")
    print("=" * 80)
    print(sdl)
    print()

    # Save SDL to file for Rust to read
    with open("schema.graphql", "w") as f:
        f.write(sdl)
    print("✅ SDL saved to schema.graphql")

    # Define test queries
    queries = [
        ("simple", "{ hello }"),
        (
            "stadium_basic",
            """
            {
                stadium(name: "Test Stadium") {
                    name
                    city
                    country
                }
            }
        """,
        ),
        (
            "stadium_with_stands",
            """
            {
                stadium {
                    name
                    city
                    stands {
                        name
                        sectionType
                        priceCategory
                    }
                }
            }
        """,
        ),
        (
            "stadium_full",
            """
            {
                stadium {
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
        """,
        ),
    ]

    # Save queries to files
    for name, query in queries:
        filename = f"query_{name}.graphql"
        with open(filename, "w") as f:
            f.write(query)
        print(f"✅ Query saved to {filename}")

    print()
    print("=" * 80)
    print("TEST EXECUTION WITH PYTHON (baseline)")
    print("=" * 80)

    # Test with Python for comparison
    import asyncio
    import time

    async def test_python_execution():
        for name, query in queries:
            print(f"\n{name}:")
            start = time.perf_counter()
            result = await schema.execute(query)
            elapsed = (time.perf_counter() - start) * 1000

            if result.errors:
                print(f"  ❌ Errors: {result.errors}")
            else:
                print(f"  ✅ Success ({elapsed:.2f}ms)")
                # Don't print full data for large responses
                if name == "simple":
                    print(f"  Data: {result.data}")

    asyncio.run(test_python_execution())

    print()
    print("=" * 80)
    print("NEXT: Run Rust execution test")
    print(
        "  cargo run --manifest-path=strawberry-core-rs/Cargo.toml --bin test_strawberry"
    )
    print("=" * 80)


if __name__ == "__main__":
    main()
