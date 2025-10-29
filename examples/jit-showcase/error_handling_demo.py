#!/usr/bin/env python
"""Demonstrates GraphQL spec-compliant error handling in the JIT compiler.

The JIT compiler now properly handles:
- Nullable field errors (field set to null)
- Non-nullable field errors (propagate to nearest nullable ancestor)
- List item errors
- Partial query success
- Error collection and reporting
"""

import os
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)


from graphql import execute_sync, parse

import strawberry

# Import JIT compilers
from strawberry.jit import compile_query

# Define schema with various error scenarios


@strawberry.type
class Product:
    id: int
    name: str

    @strawberry.field
    def price(self) -> float:
        """Non-nullable field that might error."""
        if self.id == 666:
            raise ValueError(f"Cannot price product {self.id} - it's cursed!")
        return self.id * 10.99

    @strawberry.field
    def description(self) -> str | None:
        """Nullable field that might error."""
        if self.id == 13:
            raise ValueError(f"Product {self.id} is unlucky - no description!")
        return f"This is product {self.name}"

    @strawberry.field
    def in_stock(self) -> bool:
        """Field that always works."""
        return self.id % 2 == 0


@strawberry.type
class Category:
    name: str

    @strawberry.field
    def products(self) -> list[Product]:
        """Return products, some might cause errors."""
        products = []
        if self.name == "Normal":
            products = [
                Product(id=1, name="Widget"),
                Product(id=2, name="Gadget"),
                Product(id=3, name="Doohickey"),
            ]
        elif self.name == "Unlucky":
            products = [
                Product(id=11, name="Mirror"),
                Product(id=13, name="Black Cat"),  # Will error on description
                Product(id=15, name="Ladder"),
            ]
        elif self.name == "Cursed":
            products = [
                Product(id=665, name="Almost Evil"),
                Product(id=666, name="The Beast"),  # Will error on price (non-nullable)
                Product(id=667, name="Neighbor"),
            ]
        return products


@strawberry.type
class Store:
    name: str

    @strawberry.field
    def category(self, name: str) -> Category:
        """Get category by name."""
        return Category(name=name)

    @strawberry.field
    def featured_product(self) -> Product:
        """Non-nullable field that might error."""
        if self.name == "Broken Store":
            raise Exception("This store is broken!")
        return Product(id=100, name="Featured Item")

    @strawberry.field
    def announcement(self) -> str | None:
        """Nullable field that might error."""
        if self.name == "Silent Store":
            raise Exception("No announcements available")
        return f"Welcome to {self.name}!"


@strawberry.type
class Query:
    @strawberry.field
    def store(self, name: str = "Normal Store") -> Store | None:
        """Root field is nullable."""
        return Store(name=name)

    @strawberry.field
    def required_store(self, name: str = "Normal Store") -> Store:
        """Non-nullable root field."""
        if name == "NonExistent":
            raise Exception("Store not found!")
        return Store(name=name)


def demo_nullable_field_errors() -> None:
    """Demonstrate nullable field error handling."""
    schema = strawberry.Schema(Query)

    # Query with nullable field that errors
    query = """
    query {
        store(name: "Unlucky Store") {
            name
            announcement
            category(name: "Unlucky") {
                products {
                    id
                    name
                    description
                    inStock
                }
            }
        }
    }
    """

    print("\n" + "=" * 70)
    print("ERROR HANDLING - Nullable Field Errors")
    print("=" * 70)

    # Standard execution
    result = execute_sync(schema._schema, parse(query), root_value=Query())
    if result.errors:
        print(f"Standard execution errors: {len(result.errors)} error(s) found")
        for error in result.errors[:2]:
            print(f"  - {str(error)[:60]}...")

    # JIT execution
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(Query())
    if "data" in jit_result:
        print(f"JIT returned data: {jit_result['data'] is not None}")
    if "errors" in jit_result:
        print(f"JIT execution errors: {len(jit_result['errors'])} error(s) found")
        for error in jit_result["errors"][:2]:
            print(f"  - {str(error)[:60]}...")


def demo_non_nullable_field_errors() -> None:
    """Demonstrate non-nullable field error propagation."""
    schema = strawberry.Schema(Query)

    # Query with non-nullable field that errors
    query = """
    query {
        store(name: "Cursed Store") {
            name
            category(name: "Cursed") {
                products {
                    id
                    name
                    price
                    inStock
                }
            }
        }
    }
    """

    print("\n" + "=" * 70)
    print("ERROR HANDLING - Non-Nullable Field Error Propagation")
    print("=" * 70)

    # Standard execution
    result = execute_sync(schema._schema, parse(query), root_value=Query())
    if result.errors:
        print(f"Standard execution errors: {len(result.errors)} error(s) found")
        for error in result.errors[:2]:
            print(f"  - {str(error)[:60]}...")

    # JIT execution
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(Query())
    if jit_result.get("errors"):
        print(f"JIT execution errors: {len(jit_result['errors'])} error(s) found")
        for error in jit_result["errors"][:2]:
            print(f"  - {str(error)[:60]}...")


def demo_partial_success() -> None:
    """Demonstrate partial query success with mixed errors."""
    schema = strawberry.Schema(Query)

    # Query with mix of successful and failing fields
    query = """
    query {
        normalStore: store(name: "Normal Store") {
            name
            announcement
            featuredProduct {
                id
                name
                price
            }
            category(name: "Normal") {
                products {
                    id
                    name
                    inStock
                }
            }
        }
        silentStore: store(name: "Silent Store") {
            name
            announcement
            category(name: "Unlucky") {
                products {
                    id
                    name
                    description
                }
            }
        }
    }
    """

    print("\n" + "=" * 70)
    print("ERROR HANDLING - Partial Query Success (Mixed Errors)")
    print("=" * 70)

    # JIT execution with caching
    # Simple query cache for demo

    query_cache = {}

    cache_compiler = type(
        "QueryCache",
        (),
        {
            "compile_query": lambda self, q: query_cache.setdefault(
                q, compile_query(schema, q)
            )
        },
    )()
    cached_fn = cache_compiler.compile_query(query)
    result = cached_fn(Query())

    if "data" in result:
        normal = result["data"].get("normalStore", {})
        silent = result["data"].get("silentStore", {})
        print(f"Normal store returned: {normal is not None}")
        print(f"Silent store returned: {silent is not None}")
        if normal.get("category", {}).get("products"):
            print(f"Normal store products: {len(normal['category']['products'])} items")

    if "errors" in result:
        print(f"Partial errors in response: {len(result['errors'])} error(s)")
        for i, error in enumerate(result["errors"][:3], 1):
            print(f"  Error {i}: {str(error)[:50]}...")


def demo_root_level_errors() -> None:
    """Demonstrate root-level error handling."""
    schema = strawberry.Schema(Query)

    # Query with non-nullable root that errors
    query = """
    query {
        requiredStore(name: "NonExistent") {
            name
            announcement
        }
    }
    """

    print("\n" + "=" * 70)
    print("ERROR HANDLING - Root-Level Errors")
    print("=" * 70)

    # Standard execution
    result = execute_sync(schema._schema, parse(query), root_value=Query())
    print(f"Standard execution - errors: {len(result.errors) if result.errors else 0}")
    if result.errors:
        print(f"  {str(result.errors[0])[:60]}...")

    # JIT execution
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(Query())
    if "errors" in jit_result:
        print(f"JIT execution - errors: {len(jit_result['errors'])}")
        for error in jit_result["errors"][:1]:
            print(f"  {str(error)[:60]}...")


def demo_performance_with_errors() -> None:
    """Show that error handling doesn't impact performance."""
    import time

    schema = strawberry.Schema(Query)

    # Query that will have some errors
    query = """
    query {
        store(name: "Mixed Store") {
            name
            category(name: "Unlucky") {
                products {
                    id
                    name
                    description
                    price
                    inStock
                }
            }
        }
    }
    """

    print("\n" + "=" * 70)
    print("PERFORMANCE - Error Handling Performance Comparison")
    print("=" * 70)

    # Standard execution
    iterations = 100
    start = time.perf_counter()
    for _ in range(iterations):
        execute_sync(schema._schema, parse(query), root_value=Query())
    standard_time = (time.perf_counter() - start) * 1000 / iterations

    # JIT execution
    compiled_fn = compile_query(schema, query)
    start = time.perf_counter()
    for _ in range(iterations):
        compiled_fn(Query())
    jit_time = (time.perf_counter() - start) * 1000 / iterations

    # Cached JIT
    # Simple query cache for demo

    query_cache = {}

    cache_compiler = type(
        "QueryCache",
        (),
        {
            "compile_query": lambda self, q: query_cache.setdefault(
                q, compile_query(schema, q)
            )
        },
    )()
    cached_fn = cache_compiler.compile_query(query)
    start = time.perf_counter()
    for _ in range(iterations):
        cached_fn(Query())
    cached_time = (time.perf_counter() - start) * 1000 / iterations

    print(f"Standard: {standard_time:.2f}ms per execution")
    print(f"JIT:      {jit_time:.2f}ms per execution")
    print(f"Cached:   {cached_time:.2f}ms per execution")
    print("-" * 70)
    print(f"JIT Speedup:    {standard_time / jit_time:.2f}x faster")
    print(f"Cached Speedup: {standard_time / cached_time:.2f}x faster")


def main() -> None:
    demo_nullable_field_errors()
    demo_non_nullable_field_errors()
    demo_partial_success()
    demo_root_level_errors()
    demo_performance_with_errors()


if __name__ == "__main__":
    main()
