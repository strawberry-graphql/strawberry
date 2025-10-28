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
from strawberry.jit import CachedJITCompiler, compile_query

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

    # Standard execution
    result = execute_sync(schema._schema, parse(query), root_value=Query())
    if result.errors:
        pass

    # JIT execution
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(Query())
    if "data" in jit_result:
        pass
    if "errors" in jit_result:
        pass


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

    # Standard execution
    result = execute_sync(schema._schema, parse(query), root_value=Query())
    if result.errors:
        pass

    # JIT execution
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(Query())
    if jit_result.get("errors"):
        pass


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

    # JIT execution with caching
    cache_compiler = CachedJITCompiler(schema)
    cached_fn = cache_compiler.compile_query(query)
    result = cached_fn(Query())

    if "data" in result:
        normal = result["data"].get("normalStore", {})
        result["data"].get("silentStore", {})
        if normal.get("category", {}).get("products"):
            pass

    if "errors" in result:
        for _i, _error in enumerate(result["errors"][:3], 1):
            pass


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

    # Standard execution
    execute_sync(schema._schema, parse(query), root_value=Query())

    # JIT execution
    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(Query())
    if "errors" in jit_result:
        pass


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

    # Standard execution
    iterations = 100
    start = time.perf_counter()
    for _ in range(iterations):
        execute_sync(schema._schema, parse(query), root_value=Query())
    (time.perf_counter() - start) * 1000 / iterations

    # JIT execution
    compiled_fn = compile_query(schema, query)
    start = time.perf_counter()
    for _ in range(iterations):
        compiled_fn(Query())
    (time.perf_counter() - start) * 1000 / iterations

    # Cached JIT
    cache_compiler = CachedJITCompiler(schema)
    cached_fn = cache_compiler.compile_query(query)
    start = time.perf_counter()
    for _ in range(iterations):
        cached_fn(Query())
    (time.perf_counter() - start) * 1000 / iterations


def main() -> None:
    demo_nullable_field_errors()
    demo_non_nullable_field_errors()
    demo_partial_success()
    demo_root_level_errors()
    demo_performance_with_errors()


if __name__ == "__main__":
    main()
