"""
Test complex JIT compilation scenarios with custom resolvers.
"""

import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from graphql import execute, parse
from pytest_snapshot.plugin import Snapshot

import strawberry
from strawberry.jit import JITCompiler, compile_query

HERE = Path(__file__).parent


@strawberry.type
class Product:
    id: str
    name: str
    price: float
    discount_percent: float = 0.0

    @strawberry.field
    def final_price(self) -> float:
        """Calculate price after discount."""
        return self.price * (1 - self.discount_percent / 100)

    @strawberry.field
    def savings(self) -> float:
        """Calculate savings amount."""
        return self.price * (self.discount_percent / 100)

    @strawberry.field
    def is_on_sale(self) -> bool:
        """Check if product is on sale."""
        return self.discount_percent > 0


@strawberry.type
class CartItem:
    product: Product
    quantity: int

    @strawberry.field
    def subtotal(self) -> float:
        """Calculate item subtotal."""
        return self.product.final_price() * self.quantity

    @strawberry.field
    def original_price(self) -> float:
        """Calculate original price before discount."""
        return self.product.price * self.quantity

    @strawberry.field
    def total_savings(self) -> float:
        """Calculate total savings for this item."""
        return self.product.savings() * self.quantity


@strawberry.type
class ShoppingCart:
    id: str
    items: List[CartItem]
    created_at: datetime

    @strawberry.field
    def item_count(self) -> int:
        """Total number of items in cart."""
        return sum(item.quantity for item in self.items)

    @strawberry.field
    def subtotal(self) -> float:
        """Cart subtotal before tax and shipping."""
        return sum(item.subtotal() for item in self.items)

    @strawberry.field
    def tax_amount(self) -> float:
        """Calculate tax (10%)."""
        return self.subtotal() * 0.10

    @strawberry.field
    def shipping_cost(self) -> float:
        """Calculate shipping based on subtotal."""
        subtotal = self.subtotal()
        if subtotal >= 100:
            return 0.0  # Free shipping
        if subtotal >= 50:
            return 5.99
        return 9.99

    @strawberry.field
    def total(self) -> float:
        """Calculate total including tax and shipping."""
        return self.subtotal() + self.tax_amount() + self.shipping_cost()

    @strawberry.field
    def total_savings(self) -> float:
        """Calculate total savings across all items."""
        return sum(item.total_savings() for item in self.items)

    @strawberry.field
    def free_shipping_message(self) -> Optional[str]:
        """Message about free shipping threshold."""
        subtotal = self.subtotal()
        if subtotal >= 100:
            return "You qualify for FREE shipping!"
        needed = 100 - subtotal
        return f"Add ${needed:.2f} more for FREE shipping"

    @strawberry.field
    def is_abandoned(self) -> bool:
        """Check if cart is abandoned (older than 1 day)."""
        return (datetime.now() - self.created_at).days > 1


@strawberry.type
class Analytics:
    carts: List[ShoppingCart]

    @strawberry.field
    def total_carts(self) -> int:
        """Total number of carts."""
        return len(self.carts)

    @strawberry.field
    def abandoned_carts(self) -> int:
        """Number of abandoned carts."""
        return sum(1 for cart in self.carts if cart.is_abandoned())

    @strawberry.field
    def average_cart_value(self) -> float:
        """Average cart value."""
        if not self.carts:
            return 0.0
        return sum(cart.total() for cart in self.carts) / len(self.carts)

    @strawberry.field
    def total_revenue_potential(self) -> float:
        """Total potential revenue from all carts."""
        return sum(cart.total() for cart in self.carts)

    @strawberry.field
    def most_popular_product(self) -> Optional[Product]:
        """Find the most popular product across all carts."""
        product_counts = {}
        for cart in self.carts:
            for item in cart.items:
                pid = item.product.id
                product_counts[pid] = product_counts.get(pid, 0) + item.quantity

        if not product_counts:
            return None

        # Find the most popular product
        most_popular_id = max(product_counts, key=product_counts.get)
        for cart in self.carts:
            for item in cart.items:
                if item.product.id == most_popular_id:
                    return item.product
        return None


@strawberry.type
class Query:
    @strawberry.field
    def shopping_cart(self) -> ShoppingCart:
        """Get a shopping cart with multiple items and discounts."""
        products = [
            Product(id="1", name="Laptop", price=999.99, discount_percent=10),
            Product(id="2", name="Mouse", price=29.99, discount_percent=0),
            Product(id="3", name="Keyboard", price=89.99, discount_percent=20),
            Product(id="4", name="Monitor", price=299.99, discount_percent=15),
        ]

        items = [
            CartItem(product=products[0], quantity=1),
            CartItem(product=products[1], quantity=2),
            CartItem(product=products[2], quantity=1),
            CartItem(product=products[3], quantity=1),
        ]

        return ShoppingCart(
            id="cart_123", items=items, created_at=datetime.now() - timedelta(hours=2)
        )

    @strawberry.field
    def analytics(self) -> Analytics:
        """Get analytics for multiple carts."""
        # Create sample carts
        carts = []
        for i in range(3):
            products = [
                Product(
                    id=f"p{i}_{j}",
                    name=f"Product {j}",
                    price=50.0 + (j * 25.0),
                    discount_percent=random.choice([0, 10, 20]),
                )
                for j in range(3)
            ]

            items = [
                CartItem(product=products[j], quantity=random.randint(1, 3))
                for j in range(random.randint(1, 3))
            ]

            carts.append(
                ShoppingCart(
                    id=f"cart_{i}",
                    items=items,
                    created_at=datetime.now() - timedelta(days=i),
                )
            )

        return Analytics(carts=carts)


def test_complex_shopping_cart_jit(snapshot: Snapshot):
    """Test JIT compilation with complex shopping cart example."""
    schema = strawberry.Schema(Query)

    query = """
    query GetShoppingCart {
        shoppingCart {
            id
            itemCount
            subtotal
            taxAmount
            shippingCost
            total
            totalSavings
            freeShippingMessage
            isAbandoned

            items {
                quantity
                subtotal
                originalPrice
                totalSavings

                product {
                    name
                    price
                    finalPrice
                    savings
                    isOnSale
                }
            }
        }
    }
    """

    # Compile the query
    compiler = JITCompiler(schema._schema)
    document = parse(query)
    operation = compiler._get_operation(document)
    root_type = schema._schema.type_map["Query"]

    # Generate the function code
    generated_code = compiler._generate_function(operation, root_type)

    # Check the generated code with snapshot
    snapshot.snapshot_dir = HERE / "snapshots" / "jit_complex"
    snapshot.assert_match(generated_code, "shopping_cart.py")

    # Compile with JIT
    compiled_fn = compile_query(schema._schema, query)
    root = Query()

    # Execute both ways
    jit_result = compiled_fn(root)
    standard_result = execute(schema._schema, parse(query), root_value=root)

    # Verify results match
    assert jit_result["shoppingCart"]["id"] == "cart_123"
    assert jit_result["shoppingCart"]["itemCount"] == 5
    assert jit_result["shoppingCart"]["subtotal"] > 0
    assert jit_result["shoppingCart"]["total"] > jit_result["shoppingCart"]["subtotal"]
    assert len(jit_result["shoppingCart"]["items"]) == 4

    # Check that results match between JIT and standard
    assert (
        jit_result["shoppingCart"]["total"]
        == standard_result.data["shoppingCart"]["total"]
    )
    assert (
        jit_result["shoppingCart"]["totalSavings"]
        == standard_result.data["shoppingCart"]["totalSavings"]
    )


def test_complex_analytics_jit(snapshot: Snapshot):
    """Test JIT compilation with analytics aggregations."""
    schema = strawberry.Schema(Query)

    query = """
    query GetAnalytics {
        analytics {
            totalCarts
            abandonedCarts
            averageCartValue
            totalRevenuePotential

            mostPopularProduct {
                id
                name
                price
            }

            carts {
                id
                total
                isAbandoned
                itemCount
            }
        }
    }
    """

    # Compile the query
    compiler = JITCompiler(schema._schema)
    document = parse(query)
    operation = compiler._get_operation(document)
    root_type = schema._schema.type_map["Query"]

    # Generate the function code
    generated_code = compiler._generate_function(operation, root_type)

    # Check the generated code with snapshot
    snapshot.snapshot_dir = HERE / "snapshots" / "jit_complex"
    snapshot.assert_match(generated_code, "analytics.py")

    # Compile with JIT
    compiled_fn = compile_query(schema._schema, query)
    root = Query()

    # Execute both ways with same seed
    random.seed(42)
    jit_result = compiled_fn(root)

    random.seed(42)
    standard_result = execute(schema._schema, parse(query), root_value=root)

    # Verify results
    analytics = jit_result["analytics"]
    assert analytics["totalCarts"] == 3
    assert analytics["abandonedCarts"] >= 0
    assert analytics["averageCartValue"] > 0
    assert analytics["totalRevenuePotential"] > 0
    assert len(analytics["carts"]) == 3

    # Verify JIT matches standard execution
    assert jit_result == standard_result.data


def test_performance_complex_query(snapshot: Snapshot):
    """Test that JIT provides performance benefit for complex queries."""
    schema = strawberry.Schema(Query)

    query = """
    query FullCartAnalysis {
        shoppingCart {
            id
            itemCount
            subtotal
            taxAmount
            shippingCost
            total
            totalSavings
            freeShippingMessage
            isAbandoned
            items {
                quantity
                subtotal
                originalPrice
                totalSavings
                product {
                    id
                    name
                    price
                    finalPrice
                    savings
                    isOnSale
                }
            }
        }
        analytics {
            totalCarts
            abandonedCarts
            averageCartValue
            totalRevenuePotential
            mostPopularProduct {
                id
                name
                price
            }
            carts {
                id
                total
                totalSavings
                isAbandoned
                itemCount
                items {
                    quantity
                    subtotal
                    product {
                        name
                        finalPrice
                    }
                }
            }
        }
    }
    """

    # Compile the query
    compiler = JITCompiler(schema._schema)
    document = parse(query)
    operation = compiler._get_operation(document)
    root_type = schema._schema.type_map["Query"]

    # Generate the function code
    generated_code = compiler._generate_function(operation, root_type)

    # Check the generated code with snapshot
    snapshot.snapshot_dir = HERE / "snapshots" / "jit_complex"
    snapshot.assert_match(generated_code, "full_cart_analysis.py")

    # Parse once
    parsed_query = parse(query)

    # Compile with JIT
    compiled_fn = compile_query(schema._schema, query)
    root = Query()

    # Warm up
    compiled_fn(root)
    execute(schema._schema, parsed_query, root_value=root)

    # Measure JIT performance
    iterations = 100
    jit_start = time.perf_counter()
    for _ in range(iterations):
        jit_result = compiled_fn(root)
    jit_time = time.perf_counter() - jit_start

    # Measure standard performance
    standard_start = time.perf_counter()
    for _ in range(iterations):
        standard_result = execute(schema._schema, parsed_query, root_value=root)
    standard_time = time.perf_counter() - standard_start

    # Calculate speedup
    speedup = standard_time / jit_time

    print(f"\nComplex Query Performance ({iterations} iterations):")
    print(f"  Standard GraphQL: {standard_time * 1000:.2f}ms")
    print(f"  JIT Compiled:     {jit_time * 1000:.2f}ms")
    print(f"  Speedup:          {speedup:.1f}x")

    # Assert JIT is faster
    assert jit_time < standard_time, "JIT should be faster than standard execution"
    assert speedup > 1.5, f"Expected at least 1.5x speedup, got {speedup:.1f}x"


if __name__ == "__main__":
    from pytest_snapshot.plugin import Snapshot

    # Create a mock snapshot for testing
    class MockSnapshot:
        def __init__(self):
            self.snapshot_dir = None

        def assert_match(self, content, filename):
            print(
                f"Would save snapshot to: {self.snapshot_dir / filename if self.snapshot_dir else filename}"
            )

    snapshot = MockSnapshot()

    test_complex_shopping_cart_jit(snapshot)
    test_complex_analytics_jit(snapshot)
    test_performance_complex_query(snapshot)
    print("\n✅ All complex JIT tests passed!")
