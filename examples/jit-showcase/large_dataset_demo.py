#!/usr/bin/env python
"""Large dataset demonstration showing dramatic JIT compiler benefits.
This example processes thousands of records with computed fields.
"""

import os
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import hashlib
import statistics
import time
from datetime import datetime, timedelta

from graphql import execute_sync, parse

import strawberry

# Try importing JIT
try:
    from strawberry.jit import CachedJITCompiler, compile_query

    JIT_AVAILABLE = True
except ImportError:
    JIT_AVAILABLE = False


# Schema with lots of computed fields and data
@strawberry.type
class Address:
    street: str
    city: str
    country: str
    postal_code: str

    @strawberry.field
    def full_address(self) -> str:
        """Computed field - formatted address."""
        return f"{self.street}, {self.city}, {self.country} {self.postal_code}"

    @strawberry.field
    def is_domestic(self) -> bool:
        """Check if domestic address."""
        return self.country == "USA"

    @strawberry.field
    def region(self) -> str:
        """Determine region from postal code."""
        if self.postal_code.startswith("1"):
            return "Northeast"
        if self.postal_code.startswith("2"):
            return "Mid-Atlantic"
        if self.postal_code.startswith("3"):
            return "Southeast"
        if self.postal_code.startswith("4"):
            return "Midwest"
        if self.postal_code.startswith("5"):
            return "South"
        if self.postal_code.startswith("6"):
            return "Central"
        if self.postal_code.startswith("7"):
            return "Southwest"
        if self.postal_code.startswith("8"):
            return "Mountain"
        if self.postal_code.startswith("9"):
            return "Pacific"
        return "Other"

    @strawberry.field
    def shipping_zone(self) -> int:
        """Calculate shipping zone."""
        return int(self.postal_code[0]) if self.postal_code else 5


@strawberry.type
class OrderItem:
    product_id: str
    product_name: str
    quantity: int
    unit_price: float

    @strawberry.field
    def subtotal(self) -> float:
        """Calculate line item subtotal."""
        return round(self.quantity * self.unit_price, 2)

    @strawberry.field
    def tax(self) -> float:
        """Calculate tax for this item."""
        return round(self.subtotal() * 0.08, 2)

    @strawberry.field
    def total(self) -> float:
        """Total including tax."""
        return round(self.subtotal() + self.tax(), 2)

    @strawberry.field
    def discount_amount(self) -> float:
        """Calculate bulk discount."""
        if self.quantity >= 10:
            return round(self.subtotal() * 0.1, 2)
        if self.quantity >= 5:
            return round(self.subtotal() * 0.05, 2)
        return 0.0

    @strawberry.field
    def weight(self) -> float:
        """Calculate item weight."""
        return self.quantity * 0.5

    @strawberry.field
    def volume(self) -> float:
        """Calculate shipping volume."""
        return self.quantity * 2.5

    @strawberry.field
    def is_heavy(self) -> bool:
        """Check if item is heavy."""
        return self.weight() > 10

    @strawberry.field
    def requires_special_handling(self) -> bool:
        """Check if special handling needed."""
        return self.unit_price > 100 or self.quantity > 20

    @strawberry.field
    def sku(self) -> str:
        """Generate SKU."""
        return f"SKU-{self.product_id.upper()}-{self.quantity:03d}"

    @strawberry.field
    def barcode(self) -> str:
        """Generate barcode."""
        return (
            hashlib.md5(f"{self.product_id}-{self.quantity}".encode())
            .hexdigest()[:12]
            .upper()
        )

    @strawberry.field
    def final_price(self) -> float:
        """Final price after discount and tax."""
        return round(self.total() - self.discount_amount(), 2)


@strawberry.type
class Customer:
    id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    registration_date: str
    vip_status: bool

    def __init__(
        self,
        id: str,
        first_name: str,
        last_name: str,
        email: str,
        phone: str,
        registration_date: str,
        vip_status: bool,
    ) -> None:
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
        self.registration_date = registration_date
        self.vip_status = vip_status
        self._address = None

    @strawberry.field
    def full_name(self) -> str:
        """Computed full name."""
        return f"{self.first_name} {self.last_name}"

    @strawberry.field
    def display_name(self) -> str:
        """Display name with VIP badge."""
        vip = " ⭐ VIP" if self.vip_status else ""
        return f"{self.full_name()}{vip}"

    @strawberry.field
    def masked_email(self) -> str:
        """Partially masked email for privacy."""
        parts = self.email.split("@")
        if len(parts) == 2:
            name = parts[0]
            if len(name) > 3:
                masked = name[:2] + "*" * (len(name) - 3) + name[-1]
                return f"{masked}@{parts[1]}"
        return self.email

    @strawberry.field
    def masked_phone(self) -> str:
        """Masked phone number."""
        if len(self.phone) >= 10:
            return f"***-***-{self.phone[-4:]}"
        return self.phone

    @strawberry.field
    def customer_since_days(self) -> int:
        """Days since registration."""
        reg_date = datetime.fromisoformat(self.registration_date)
        return (datetime.now() - reg_date).days

    @strawberry.field
    def loyalty_tier(self) -> str:
        """Calculate loyalty tier based on registration."""
        days = self.customer_since_days()
        if days > 365:
            return "Platinum"
        if days > 180:
            return "Gold"
        if days > 90:
            return "Silver"
        return "Bronze"

    @strawberry.field
    def loyalty_points(self) -> int:
        """Calculate loyalty points."""
        base = self.customer_since_days() * 10
        if self.vip_status:
            return base * 2
        return base

    @strawberry.field
    def next_tier_days(self) -> int:
        """Days until next tier."""
        days = self.customer_since_days()
        if days > 365:
            return 0
        if days > 180:
            return 365 - days
        if days > 90:
            return 180 - days
        return 90 - days

    @strawberry.field
    def discount_percentage(self) -> float:
        """Customer discount based on tier."""
        tier = self.loyalty_tier()
        if tier == "Platinum":
            return 15.0
        if tier == "Gold":
            return 10.0
        if tier == "Silver":
            return 5.0
        return 0.0

    @strawberry.field
    def credit_limit(self) -> float:
        """Calculate credit limit."""
        base = 1000.0
        if self.vip_status:
            base *= 5
        tier_multiplier = {"Platinum": 4, "Gold": 3, "Silver": 2, "Bronze": 1}
        return base * tier_multiplier.get(self.loyalty_tier(), 1)

    @strawberry.field
    def risk_score(self) -> int:
        """Calculate customer risk score."""
        score = 100
        if self.vip_status:
            score -= 30
        days = self.customer_since_days()
        if days > 365:
            score -= 40
        elif days > 180:
            score -= 30
        elif days > 90:
            score -= 20
        else:
            score -= 10
        return max(0, score)

    @strawberry.field
    def address(self) -> Address:
        """Customer address."""
        if not self._address:
            # Use customer ID to generate consistent address
            num = (
                int("".join(filter(str.isdigit, self.id)))
                if any(c.isdigit() for c in self.id)
                else 1
            )
            self._address = Address(
                street=f"{(num * 17) % 999 + 1} Main St",
                city=["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"][
                    num % 5
                ],
                country="USA",
                postal_code=f"{10000 + (num * 1337) % 89999}",
            )
        return self._address


@strawberry.type
class Order:
    id: str
    customer_id: str
    order_date: str
    status: str
    shipping_method: str

    def __init__(
        self,
        id: str,
        customer_id: str,
        order_date: str,
        status: str,
        shipping_method: str,
    ) -> None:
        self.id = id
        self.customer_id = customer_id
        self.order_date = order_date
        self.status = status
        self.shipping_method = shipping_method
        self._items = None
        self._customer = None

    @strawberry.field
    def order_number(self) -> str:
        """Formatted order number."""
        return f"ORD-{self.id.upper()}"

    @strawberry.field
    def status_emoji(self) -> str:
        """Status with emoji."""
        emojis = {
            "pending": "⏳",
            "processing": "🔄",
            "shipped": "📦",
            "delivered": "✅",
            "cancelled": "❌",
        }
        return f"{emojis.get(self.status, '❓')} {self.status.upper()}"

    @strawberry.field
    def days_since_order(self) -> int:
        """Days since order was placed."""
        order_dt = datetime.fromisoformat(self.order_date)
        return (datetime.now() - order_dt).days

    @strawberry.field
    def is_recent(self) -> bool:
        """Check if order is recent (< 7 days)."""
        return self.days_since_order() < 7

    @strawberry.field
    def estimated_delivery(self) -> str:
        """Calculate estimated delivery date."""
        order_dt = datetime.fromisoformat(self.order_date)
        if self.shipping_method == "express":
            delivery = order_dt + timedelta(days=2)
        elif self.shipping_method == "standard":
            delivery = order_dt + timedelta(days=5)
        else:
            delivery = order_dt + timedelta(days=10)
        return delivery.isoformat()

    @strawberry.field
    def items(self) -> list[OrderItem]:
        """Order items with calculations."""
        if not self._items:
            # Use order ID to generate consistent items
            num = (
                int("".join(filter(str.isdigit, self.id)))
                if any(c.isdigit() for c in self.id)
                else 1
            )
            # Generate 10-30 items per order for more field resolutions
            num_items = 10 + (num % 21)
            self._items = []
            for i in range(num_items):
                self._items.append(
                    OrderItem(
                        product_id=f"prod-{i}",
                        product_name=f"Product {i}",
                        quantity=1 + ((num + i) * 7) % 20,
                        unit_price=round(9.99 + ((num + i) * 13.37) % 190, 2),
                    )
                )
        return self._items

    @strawberry.field
    def item_count(self) -> int:
        """Total number of items."""
        return sum(item.quantity for item in self.items())

    @strawberry.field
    def subtotal(self) -> float:
        """Order subtotal before tax."""
        return round(sum(item.subtotal() for item in self.items()), 2)

    @strawberry.field
    def tax_amount(self) -> float:
        """Total tax."""
        return round(sum(item.tax() for item in self.items()), 2)

    @strawberry.field
    def discount_amount(self) -> float:
        """Total discounts."""
        return round(sum(item.discount_amount() for item in self.items()), 2)

    @strawberry.field
    def shipping_cost(self) -> float:
        """Calculate shipping cost."""
        if self.shipping_method == "express":
            return 29.99
        if self.shipping_method == "standard":
            return 9.99
        return 4.99

    @strawberry.field
    def total(self) -> float:
        """Grand total."""
        return round(
            self.subtotal()
            + self.tax_amount()
            - self.discount_amount()
            + self.shipping_cost(),
            2,
        )

    @strawberry.field
    def priority_score(self) -> int:
        """Calculate order priority."""
        score = 0
        if self.shipping_method == "express":
            score += 100
        elif self.shipping_method == "standard":
            score += 50
        if self.status == "pending":
            score += 20
        if self.total() > 500:
            score += 30
        return score

    @strawberry.field
    def fulfillment_center(self) -> str:
        """Determine fulfillment center."""
        # Use order ID to determine center consistently
        num = (
            int("".join(filter(str.isdigit, self.id)))
            if any(c.isdigit() for c in self.id)
            else 0
        )
        centers = ["NYC-01", "LAX-02", "CHI-03", "DAL-04", "PHX-05"]
        return centers[num % 5]

    @strawberry.field
    def tracking_number(self) -> str:
        """Generate tracking number."""
        if self.status in ["shipped", "delivered"]:
            return hashlib.md5(f"TRACK-{self.id}".encode()).hexdigest()[:10].upper()
        return "PENDING"

    @strawberry.field
    def estimated_weight(self) -> float:
        """Calculate total order weight."""
        return sum(item.weight() for item in self.items())

    @strawberry.field
    def estimated_volume(self) -> float:
        """Calculate total shipping volume."""
        return sum(item.volume() for item in self.items())

    @strawberry.field
    def requires_signature(self) -> bool:
        """Check if signature required."""
        return self.total() > 250 or any(
            item.requires_special_handling() for item in self.items()
        )

    @strawberry.field
    def insurance_amount(self) -> float:
        """Calculate insurance needed."""
        if self.total() > 100:
            return round(self.total() * 0.01, 2)
        return 0.0

    @strawberry.field
    def customer(self) -> Customer:
        """Get customer for this order."""
        if not self._customer:
            # Use customer_id to generate consistent customer data
            cust_num = (
                int("".join(filter(str.isdigit, self.customer_id)))
                if any(c.isdigit() for c in self.customer_id)
                else 0
            )
            self._customer = Customer(
                id=self.customer_id,
                first_name=f"Customer{self.customer_id}",
                last_name=["Smith", "Johnson", "Williams", "Brown", "Jones"][
                    cust_num % 5
                ],
                email=f"customer{self.customer_id}@example.com",
                phone=f"555-{1000 + (cust_num * 23) % 9000:04d}",
                registration_date=(
                    datetime.now() - timedelta(days=1 + (cust_num * 37) % 500)
                ).isoformat(),
                vip_status=(cust_num % 5) == 0,
            )
        return self._customer


@strawberry.type
class Analytics:
    def __init__(self) -> None:
        self._total_revenue = None

    @strawberry.field
    def total_orders(self) -> int:
        """Total number of orders."""
        return 10000

    @strawberry.field
    def total_revenue(self) -> float:
        """Calculate total revenue."""
        if self._total_revenue is None:
            self._total_revenue = 2547836.42
        return self._total_revenue

    @strawberry.field
    def average_order_value(self) -> float:
        """Average order value."""
        return round(self.total_revenue() / self.total_orders(), 2)

    @strawberry.field
    def conversion_rate(self) -> float:
        """Conversion rate percentage."""
        return 3.74

    @strawberry.field
    def top_products(self) -> list[str]:
        """Top selling products."""
        return [f"Product {i}" for i in range(1, 51)]

    @strawberry.field
    def growth_rate(self) -> float:
        """Month over month growth."""
        return 12.5

    @strawberry.field
    def churn_rate(self) -> float:
        """Customer churn rate."""
        return 2.1

    @strawberry.field
    def customer_lifetime_value(self) -> float:
        """Average CLV."""
        return 1245.67

    @strawberry.field
    def cart_abandonment_rate(self) -> float:
        """Cart abandonment percentage."""
        return 68.3

    @strawberry.field
    def repeat_purchase_rate(self) -> float:
        """Repeat purchase percentage."""
        return 42.7


@strawberry.type
class Query:
    @strawberry.field
    def orders(self, limit: int = 100, offset: int = 0) -> list[Order]:
        """Get orders with full details."""
        orders = []
        statuses = ["pending", "processing", "shipped", "delivered", "cancelled"]
        shipping = ["express", "standard", "economy"]

        for i in range(offset, offset + limit):
            orders.append(
                Order(
                    id=f"{i:06d}",
                    customer_id=f"{i % 200}",  # 200 unique customers
                    order_date=(
                        datetime.now() - timedelta(days=(i * 7) % 30)
                    ).isoformat(),
                    status=statuses[i % 5],
                    shipping_method=shipping[i % 3],
                )
            )
        return orders

    @strawberry.field
    def customers(self, limit: int = 100) -> list[Customer]:
        """Get customer list."""
        customers = []
        for i in range(limit):
            customers.append(
                Customer(
                    id=f"cust-{i:04d}",
                    first_name=f"John{i}",
                    last_name=["Smith", "Johnson", "Williams", "Brown", "Jones"][i % 5],
                    email=f"customer{i}@example.com",
                    phone=f"555-{1000 + i:04d}",
                    registration_date=(
                        datetime.now() - timedelta(days=1 + (i * 29) % 500)
                    ).isoformat(),
                    vip_status=i % 10 == 0,
                )
            )
        return customers

    @strawberry.field
    def analytics(self) -> Analytics:
        """Get analytics data."""
        return Analytics()


def run_large_dataset_benchmark() -> None:
    """Benchmark with large dataset."""
    schema = strawberry.Schema(Query)

    # Query that processes LOTS of data with many computed fields
    query = """
    query LargeDataset {
        orders(limit: 1000) {
            id
            orderNumber
            statusEmoji
            daysSinceOrder
            isRecent
            estimatedDelivery
            itemCount
            subtotal
            taxAmount
            discountAmount
            shippingCost
            total
            priorityScore
            fulfillmentCenter
            trackingNumber
            estimatedWeight
            estimatedVolume
            requiresSignature
            insuranceAmount

            customer {
                id
                fullName
                displayName
                maskedEmail
                maskedPhone
                customerSinceDays
                loyaltyTier
                loyaltyPoints
                nextTierDays
                discountPercentage
                creditLimit
                riskScore
                vipStatus

                address {
                    fullAddress
                    isDomestic
                    region
                    shippingZone
                }
            }

            items {
                productId
                productName
                quantity
                unitPrice
                subtotal
                tax
                total
                discountAmount
                finalPrice
                weight
                volume
                isHeavy
                requiresSpecialHandling
                sku
                barcode
            }
        }

        customers(limit: 500) {
            id
            fullName
            displayName
            maskedEmail
            loyaltyTier
            loyaltyPoints
            discountPercentage
            creditLimit
            riskScore
            address {
                fullAddress
                region
                shippingZone
            }
        }

        analytics {
            totalOrders
            totalRevenue
            averageOrderValue
            conversionRate
            topProducts
            growthRate
            churnRate
            customerLifetimeValue
            cartAbandonmentRate
            repeatPurchaseRate
        }
    }
    """

    root = Query()

    # Warm up
    for _ in range(3):
        execute_sync(schema._schema, parse(query), root_value=root)

    # 1. Standard GraphQL
    iterations = 5
    times = []
    for i in range(iterations):
        start = time.perf_counter()
        execute_sync(schema._schema, parse(query), root_value=root)
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    standard_avg = statistics.mean(times) * 1000
    min(times) * 1000
    max(times) * 1000

    # Count approximate field resolutions
    orders_fields = 1000 * 17  # 17 fields per order
    customer_fields = (
        1500 * 12
    )  # 12 fields per customer (1000 from orders + 500 from query)
    address_fields = 1500 * 4  # 4 fields per address
    items_fields = 20000 * 15  # ~20 items per order * 15 fields
    analytics_fields = 10
    total_fields = (
        orders_fields
        + customer_fields
        + address_fields
        + items_fields
        + analytics_fields
    )

    if not JIT_AVAILABLE:
        return

    # 2. JIT Compiled
    start_compile = time.perf_counter()
    compiled_fn = compile_query(schema._schema, query)
    (time.perf_counter() - start_compile) * 1000

    times = []
    for i in range(iterations):
        start = time.perf_counter()
        compiled_fn(root)
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    jit_avg = statistics.mean(times) * 1000
    min(times) * 1000
    max(times) * 1000

    # 3. Production simulation with cache
    compiler = CachedJITCompiler(schema._schema, enable_parallel=False)

    times = []
    for i in range(20):
        start = time.perf_counter()
        fn = compiler.compile_query(query)
        fn(root)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        if i == 0:
            pass

    statistics.mean(times) * 1000
    avg_cached = statistics.mean(times[1:]) * 1000  # Exclude first

    compiler.get_cache_stats()

    # Summary

    standard_avg / jit_avg
    standard_avg / avg_cached

    (1_000_000 / total_fields) * standard_avg / 1000
    (1_000_000 / total_fields) * jit_avg / 1000
    (1_000_000 / total_fields) * avg_cached / 1000

    requests = 1_000_000
    cost_per_second = 0.001  # $0.001 per CPU second

    total_time_standard = (requests * standard_avg) / 1000
    total_time_jit = (requests * jit_avg) / 1000
    total_time_cached = (requests * avg_cached) / 1000

    total_time_standard * cost_per_second
    total_time_jit * cost_per_second
    total_time_cached * cost_per_second


if __name__ == "__main__":
    run_large_dataset_benchmark()
