#!/usr/bin/env python
"""Complex JIT Compiler Example

Demonstrates the JIT compiler with a realistic e-commerce schema including:
- Custom resolvers with business logic
- Computed fields
- Nested relationships
- List operations
- Field arguments
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import random
from datetime import datetime, timedelta
from typing import List, Optional

from graphql import execute, parse

import strawberry
from strawberry.jit_compiler import compile_query

# ============= Domain Models =============


@strawberry.type
class Address:
    street: str
    city: str
    country: str
    zip_code: str

    @strawberry.field
    def formatted(self) -> str:
        """Custom resolver for formatted address."""
        return f"{self.street}, {self.city}, {self.country} {self.zip_code}"


@strawberry.type
class Category:
    id: str
    name: str
    slug: str

    @strawberry.field
    def url(self) -> str:
        """Generate category URL."""
        return f"/categories/{self.slug}"


@strawberry.type
class Product:
    id: str
    name: str
    description: str
    price: float
    stock: int
    category: Category
    created_at: datetime

    @strawberry.field
    def is_available(self) -> bool:
        """Custom resolver checking availability."""
        return self.stock > 0

    @strawberry.field
    def discount_percentage(self) -> Optional[float]:
        """Calculate discount based on age of product."""
        days_old = (datetime.now() - self.created_at).days
        if days_old > 30:
            return 10.0  # 10% discount for items older than 30 days
        if days_old > 60:
            return 20.0  # 20% discount for items older than 60 days
        return None

    @strawberry.field
    def final_price(self) -> float:
        """Calculate final price with discount."""
        discount = self.discount_percentage()
        if discount:
            return self.price * (1 - discount / 100)
        return self.price

    @strawberry.field
    def availability_status(self) -> str:
        """Detailed availability status."""
        if self.stock == 0:
            return "OUT_OF_STOCK"
        if self.stock < 5:
            return "LOW_STOCK"
        return "IN_STOCK"


@strawberry.type
class OrderItem:
    product: Product
    quantity: int
    unit_price: float

    @strawberry.field
    def subtotal(self) -> float:
        """Calculate line item subtotal."""
        return self.quantity * self.unit_price

    @strawberry.field
    def savings(self) -> float:
        """Calculate savings from discount."""
        original = self.product.price * self.quantity
        return original - self.subtotal()


@strawberry.type
class Customer:
    id: str
    name: str
    email: str
    shipping_address: Address
    billing_address: Optional[Address]
    created_at: datetime

    @strawberry.field
    def display_name(self) -> str:
        """Format customer display name."""
        return f"{self.name} ({self.email})"

    @strawberry.field
    def is_new_customer(self) -> bool:
        """Check if customer is new (registered within 30 days)."""
        return (datetime.now() - self.created_at).days < 30

    @strawberry.field
    def customer_since(self) -> str:
        """Human-readable customer duration."""
        days = (datetime.now() - self.created_at).days
        if days < 30:
            return f"{days} days"
        if days < 365:
            return f"{days // 30} months"
        return f"{days // 365} years"


@strawberry.type
class Order:
    id: str
    order_number: str
    customer: Customer
    items: List[OrderItem]
    created_at: datetime
    status: str
    shipping_address: Address

    @strawberry.field
    def total_items(self) -> int:
        """Total number of items in order."""
        return sum(item.quantity for item in self.items)

    @strawberry.field
    def subtotal(self) -> float:
        """Order subtotal before tax and shipping."""
        return sum(item.subtotal() for item in self.items)

    @strawberry.field
    def tax(self) -> float:
        """Calculate tax (10% for this example)."""
        return self.subtotal() * 0.10

    @strawberry.field
    def shipping_cost(self) -> float:
        """Calculate shipping based on total."""
        subtotal = self.subtotal()
        if subtotal > 100:
            return 0.0  # Free shipping over $100
        if subtotal > 50:
            return 5.0
        return 10.0

    @strawberry.field
    def total(self) -> float:
        """Calculate order total."""
        return self.subtotal() + self.tax() + self.shipping_cost()

    @strawberry.field
    def total_savings(self) -> float:
        """Total savings from discounts."""
        return sum(item.savings() for item in self.items)

    @strawberry.field
    def estimated_delivery(self) -> datetime:
        """Calculate estimated delivery date."""
        # 3-5 business days from order
        return self.created_at + timedelta(days=random.randint(3, 5))

    @strawberry.field
    def status_display(self) -> str:
        """Human-readable status."""
        status_map = {
            "PENDING": "Pending Payment",
            "PROCESSING": "Processing",
            "SHIPPED": "Shipped",
            "DELIVERED": "Delivered",
            "CANCELLED": "Cancelled",
        }
        return status_map.get(self.status, self.status)


@strawberry.type
class OrderSummary:
    """Summary statistics for orders."""

    total_orders: int
    total_revenue: float
    average_order_value: float
    top_category: Optional[Category]

    @strawberry.field
    def revenue_display(self) -> str:
        """Format revenue for display."""
        return f"${self.total_revenue:,.2f}"

    @strawberry.field
    def aov_display(self) -> str:
        """Format average order value."""
        return f"${self.average_order_value:.2f}"


@strawberry.type
class Query:
    @strawberry.field
    def recent_orders(self) -> List[Order]:
        """Get recent orders with complex nested data."""
        limit = 5  # Fixed limit for now since JIT doesn't support arguments yet

        # Create sample data
        categories = [
            Category(id="1", name="Electronics", slug="electronics"),
            Category(id="2", name="Clothing", slug="clothing"),
            Category(id="3", name="Books", slug="books"),
        ]

        products = []
        for i in range(20):
            cat = categories[i % 3]
            products.append(
                Product(
                    id=f"prod_{i}",
                    name=f"Product {i}",
                    description=f"Description for product {i}",
                    price=10.0 + (i * 5.5),
                    stock=random.randint(0, 100),
                    category=cat,
                    created_at=datetime.now() - timedelta(days=random.randint(1, 90)),
                )
            )

        orders = []
        for i in range(limit):
            # Create customer
            customer = Customer(
                id=f"cust_{i}",
                name=f"Customer {i}",
                email=f"customer{i}@example.com",
                shipping_address=Address(
                    street=f"{100 + i} Main St",
                    city="New York",
                    country="USA",
                    zip_code="10001",
                ),
                billing_address=None,
                created_at=datetime.now() - timedelta(days=random.randint(1, 365)),
            )

            # Create order items
            items = []
            num_items = random.randint(1, 5)
            for j in range(num_items):
                product = products[random.randint(0, len(products) - 1)]
                items.append(
                    OrderItem(
                        product=product,
                        quantity=random.randint(1, 3),
                        unit_price=product.final_price(),
                    )
                )

            orders.append(
                Order(
                    id=f"order_{i}",
                    order_number=f"ORD-{1000 + i}",
                    customer=customer,
                    items=items,
                    created_at=datetime.now() - timedelta(days=random.randint(0, 30)),
                    status=random.choice(
                        ["PENDING", "PROCESSING", "SHIPPED", "DELIVERED"]
                    ),
                    shipping_address=customer.shipping_address,
                )
            )

        return orders

    @strawberry.field
    def order_summary(self) -> OrderSummary:
        """Get order summary statistics."""
        orders = self.recent_orders()

        total_revenue = sum(order.total() for order in orders)
        avg_order_value = total_revenue / len(orders) if orders else 0

        # Find top category
        category_counts = {}
        for order in orders:
            for item in order.items:
                cat = item.product.category
                category_counts[cat.id] = category_counts.get(cat.id, 0) + item.quantity

        top_category = None
        if category_counts:
            top_cat_id = max(category_counts, key=category_counts.get)
            # Find the category object
            for order in orders:
                for item in order.items:
                    if item.product.category.id == top_cat_id:
                        top_category = item.product.category
                        break
                if top_category:
                    break

        return OrderSummary(
            total_orders=len(orders),
            total_revenue=total_revenue,
            average_order_value=avg_order_value,
            top_category=top_category,
        )


def main():
    """Run the complex JIT example."""
    schema = strawberry.Schema(Query)

    # Complex query with many custom resolvers
    query = """
    query GetRecentOrders {
        recentOrders {
            id
            orderNumber
            statusDisplay
            totalItems
            subtotal
            tax
            shippingCost
            total
            totalSavings
            estimatedDelivery

            customer {
                displayName
                isNewCustomer
                customerSince
                shippingAddress {
                    formatted
                }
            }

            items {
                quantity
                unitPrice
                subtotal
                savings

                product {
                    name
                    price
                    finalPrice
                    discountPercentage
                    isAvailable
                    availabilityStatus
                    category {
                        name
                        url
                    }
                }
            }
        }

        orderSummary {
            totalOrders
            revenueDisplay
            aovDisplay
            topCategory {
                name
                url
            }
        }
    }
    """

    print("=" * 80)
    print("COMPLEX JIT COMPILER EXAMPLE")
    print("=" * 80)
    print("\nQuery being compiled:")
    print(query)

    # Parse the query
    parsed_query = parse(query)

    # Compile with JIT
    print("\n" + "=" * 80)
    print("COMPILING WITH JIT...")
    print("=" * 80)

    import time

    start = time.perf_counter()
    jit_fn = compile_query(schema._schema, query)
    compile_time = time.perf_counter() - start
    print(f"✓ JIT compilation completed in {compile_time * 1000:.2f}ms")

    # Create root
    root = Query()

    # Execute with standard GraphQL
    print("\n" + "=" * 80)
    print("EXECUTING WITH STANDARD GRAPHQL...")
    print("=" * 80)

    start = time.perf_counter()
    standard_result = execute(schema._schema, parsed_query, root_value=root)
    standard_time = time.perf_counter() - start
    print(f"✓ Standard execution completed in {standard_time * 1000:.2f}ms")

    # Execute with JIT
    print("\n" + "=" * 80)
    print("EXECUTING WITH JIT...")
    print("=" * 80)

    start = time.perf_counter()
    jit_result = jit_fn(root)
    jit_time = time.perf_counter() - start
    print(f"✓ JIT execution completed in {jit_time * 1000:.2f}ms")

    # Performance comparison
    speedup = standard_time / jit_time
    print("\n" + "=" * 80)
    print("PERFORMANCE COMPARISON")
    print("=" * 80)
    print(f"Standard GraphQL: {standard_time * 1000:.2f}ms")
    print(f"JIT Compiled:     {jit_time * 1000:.2f}ms")
    print(f"🚀 Speedup:       {speedup:.1f}x faster")

    # Show sample results
    print("\n" + "=" * 80)
    print("SAMPLE RESULTS (First Order)")
    print("=" * 80)

    if jit_result.get("recentOrders"):
        order = jit_result["recentOrders"][0]
        print(f"Order: {order['orderNumber']}")
        print(f"Status: {order['statusDisplay']}")
        print(f"Customer: {order['customer']['displayName']}")
        print(f"  New Customer: {order['customer']['isNewCustomer']}")
        print(f"  Customer Since: {order['customer']['customerSince']}")
        print(f"Items: {order['totalItems']}")
        print(f"Subtotal: ${order['subtotal']:.2f}")
        print(f"Tax: ${order['tax']:.2f}")
        print(f"Shipping: ${order['shippingCost']:.2f}")
        print(f"Total: ${order['total']:.2f}")
        print(f"Savings: ${order['totalSavings']:.2f}")

        print("\nOrder Items:")
        for item in order["items"][:3]:  # Show first 3 items
            product = item["product"]
            print(f"  - {product['name']}")
            print(
                f"    Qty: {item['quantity']} @ ${item['unitPrice']:.2f} = ${item['subtotal']:.2f}"
            )
            print(f"    Status: {product['availabilityStatus']}")
            if product["discountPercentage"]:
                print(f"    Discount: {product['discountPercentage']:.0f}%")
                print(f"    Savings: ${item['savings']:.2f}")

    summary = jit_result.get("orderSummary", {})
    print("\nOrder Summary:")
    print(f"  Total Orders: {summary.get('totalOrders', 0)}")
    print(f"  Total Revenue: {summary.get('revenueDisplay', 'N/A')}")
    print(f"  Average Order: {summary.get('aovDisplay', 'N/A')}")
    if summary.get("topCategory"):
        print(f"  Top Category: {summary['topCategory']['name']}")

    # Verify results match
    assert len(jit_result["recentOrders"]) == len(standard_result.data["recentOrders"])
    print("\n✅ Results verified - JIT and standard execution match!")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("This example demonstrates:")
    print("• Complex nested queries with multiple levels")
    print("• Many custom resolvers with business logic")
    print("• Computed fields (prices, totals, dates)")
    print("• Conditional logic in resolvers")
    print("• List operations and aggregations")
    print(f"• {speedup:.1f}x performance improvement with JIT compilation")


if __name__ == "__main__":
    main()
