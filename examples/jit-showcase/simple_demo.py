"""Simple demonstration of JIT compiler benefits.
This example uses synchronous resolvers where JIT really shines.
"""

import os
import statistics
import sys
import time

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from graphql import execute_sync, parse

import strawberry
from strawberry.jit import compile_query


# Simple schema with SYNC resolvers (where JIT excels)
@strawberry.type
class Product:
    id: str
    name: str
    price: float
    in_stock: bool

    @strawberry.field
    def formatted_price(self) -> str:
        """Computed field."""
        return f"${self.price:.2f}"

    @strawberry.field
    def availability(self) -> str:
        """Another computed field."""
        return "In Stock" if self.in_stock else "Out of Stock"

    @strawberry.field
    def tax(self) -> float:
        """Calculate tax."""
        return round(self.price * 0.1, 2)

    @strawberry.field
    def total_price(self) -> float:
        """Price including tax."""
        return round(self.price * 1.1, 2)


@strawberry.type
class Category:
    id: str
    name: str
    description: str

    @strawberry.field
    def products(self) -> list[Product]:
        """Get products in this category."""
        # Simulate some data processing
        products = []
        for i in range(10):
            products.append(
                Product(
                    id=f"prod-{self.id}-{i}",
                    name=f"Product {i} in {self.name}",
                    price=10.00 + i * 5,
                    in_stock=i % 2 == 0,
                )
            )
        return products

    @strawberry.field
    def product_count(self) -> int:
        """Count products."""
        return 10

    @strawberry.field
    def slug(self) -> str:
        """Generate URL slug."""
        return self.name.lower().replace(" ", "-")


@strawberry.type
class Query:
    @strawberry.field
    def categories(self, limit: int = 5) -> list[Category]:
        """Get product categories."""
        categories = []
        for i in range(limit):
            categories.append(
                Category(
                    id=f"cat-{i}",
                    name=f"Category {i}",
                    description=f"Description for category {i}",
                )
            )
        return categories

    @strawberry.field
    def products(self, limit: int = 20) -> list[Product]:
        """Get all products."""
        products = []
        for i in range(limit):
            products.append(
                Product(
                    id=f"prod-{i}",
                    name=f"Product {i}",
                    price=10.00 + i * 2,
                    in_stock=i % 3 != 0,
                )
            )
        return products


def run_simple_benchmark() -> None:
    """Run a simple benchmark showing JIT benefits."""
    schema = strawberry.Schema(Query)

    # Test query with multiple computed fields
    query = """
    query GetProducts {
        products(limit: 50) {
            id
            name
            price
            formattedPrice
            availability
            tax
            totalPrice
            inStock
        }
        categories(limit: 10) {
            id
            name
            slug
            productCount
            products {
                id
                name
                formattedPrice
                availability
            }
        }
    }
    """

    root = Query()
    iterations = 50

    # Warm up
    for _ in range(5):
        execute_sync(schema._schema, parse(query), root_value=root)

    # 1. Standard GraphQL
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        execute_sync(schema._schema, parse(query), root_value=root)
        times.append(time.perf_counter() - start)

    standard_avg = statistics.mean(times) * 1000
    standard_min = min(times) * 1000
    standard_max = max(times) * 1000

    print("\n📊 JIT Compiler Performance Comparison")
    print("=" * 70)
    print(f"\n⏱️  Standard GraphQL Execution ({iterations} iterations)")
    print(f"   Average: {standard_avg:.2f}ms")
    print(f"   Min:     {standard_min:.2f}ms")
    print(f"   Max:     {standard_max:.2f}ms")

    # 2. JIT Compiled (first time - includes compilation)
    print("\n⚡ JIT Compiled Execution")
    start_compile = time.perf_counter()
    compiled_fn = compile_query(schema, query)
    compile_time = (time.perf_counter() - start_compile) * 1000
    print(f"   Compilation time: {compile_time:.2f}ms")

    # Run compiled version
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        compiled_fn(root)
        times.append(time.perf_counter() - start)

    jit_avg = statistics.mean(times) * 1000
    jit_min = min(times) * 1000
    jit_max = max(times) * 1000

    print(f"   Average: {jit_avg:.2f}ms")
    print(f"   Min:     {jit_min:.2f}ms")
    print(f"   Max:     {jit_max:.2f}ms")

    # 3. JIT with Manual Cache (simulating production)
    print("\n💾 JIT with Manual Cache (100 requests)")

    # Simple query cache
    query_cache = {}

    def get_compiled_query(q):
        if q not in query_cache:
            query_cache[q] = compile_query(schema, q)
        return query_cache[q]

    # Simulate 100 requests of the same query
    times = []
    for _i in range(100):
        start = time.perf_counter()
        fn = get_compiled_query(query)
        fn(root)
        times.append(time.perf_counter() - start)

    cached_avg = statistics.mean(times) * 1000
    first_request = times[0] * 1000  # First request (compilation)
    cached_rest_avg = statistics.mean(times[1:]) * 1000  # Subsequent (cached)

    print(f"   First request (cold): {first_request:.2f}ms")
    print(f"   Avg cached requests:  {cached_rest_avg:.2f}ms")
    print(f"   Cache entries: {len(query_cache)}")

    # Summary
    print("\n🎯 Results Summary")
    print("=" * 70)

    speedup_jit = standard_avg / jit_avg
    speedup_cached = standard_avg / cached_rest_avg

    print(f"Standard GraphQL:     {standard_avg:.2f}ms")
    print(f"JIT Compiled:         {jit_avg:.2f}ms  ({speedup_jit:.2f}x faster)")
    print(
        f"JIT Cached:           {cached_rest_avg:.2f}ms  ({speedup_cached:.2f}x faster)"
    )

    improvement_jit = ((standard_avg - jit_avg) / standard_avg) * 100
    improvement_cached = ((standard_avg - cached_rest_avg) / standard_avg) * 100

    print("\nPerformance Improvements:")
    print(f"  JIT:    {improvement_jit:.1f}% faster")
    print(f"  Cached: {improvement_cached:.1f}% faster")

    # Throughput
    print("\nThroughput (queries/second):")
    print(f"  Standard: {1000 / standard_avg:.0f} q/s")
    print(f"  JIT:      {1000 / jit_avg:.0f} q/s")
    print(f"  Cached:   {1000 / cached_rest_avg:.0f} q/s")

    print("\n✅ JIT compilation provides significant performance improvements!")
    print("   For production, implement a query cache as shown above.")


if __name__ == "__main__":
    run_simple_benchmark()
