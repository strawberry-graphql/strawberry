"""
Simple demonstration of JIT compiler benefits.
This example uses synchronous resolvers where JIT really shines.
"""

import time
import statistics
from typing import List

import strawberry
from graphql import execute_sync, parse

# Try importing JIT compilers
try:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from strawberry.jit_compiler import compile_query
    from strawberry.jit_compiler_cached import CachedJITCompiler
    JIT_AVAILABLE = True
except ImportError:
    print("⚠️  JIT compiler not available")
    JIT_AVAILABLE = False


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
    def products(self) -> List[Product]:
        """Get products in this category."""
        # Simulate some data processing
        products = []
        for i in range(10):
            products.append(Product(
                id=f"prod-{self.id}-{i}",
                name=f"Product {i} in {self.name}",
                price=10.00 + i * 5,
                in_stock=i % 2 == 0
            ))
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
    def categories(self, limit: int = 5) -> List[Category]:
        """Get product categories."""
        categories = []
        for i in range(limit):
            categories.append(Category(
                id=f"cat-{i}",
                name=f"Category {i}",
                description=f"Description for category {i}"
            ))
        return categories
    
    @strawberry.field
    def products(self, limit: int = 20) -> List[Product]:
        """Get all products."""
        products = []
        for i in range(limit):
            products.append(Product(
                id=f"prod-{i}",
                name=f"Product {i}",
                price=10.00 + i * 2,
                in_stock=i % 3 != 0
            ))
        return products


def run_simple_benchmark():
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
    
    print("\n" + "="*60)
    print("⚡ SYNCHRONOUS QUERY PERFORMANCE COMPARISON")
    print("="*60)
    print("\nThis demonstrates where JIT compilation really shines:")
    print("Synchronous queries with many field resolutions.\n")
    
    root = Query()
    iterations = 50
    
    # Warm up
    for _ in range(5):
        execute_sync(schema._schema, parse(query), root_value=root)
    
    # 1. Standard GraphQL
    print("Running standard GraphQL execution...")
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        result = execute_sync(schema._schema, parse(query), root_value=root)
        times.append(time.perf_counter() - start)
    
    standard_avg = statistics.mean(times) * 1000
    standard_min = min(times) * 1000
    standard_max = max(times) * 1000
    
    print(f"✅ Standard GraphQL:")
    print(f"   Average: {standard_avg:.2f}ms")
    print(f"   Min:     {standard_min:.2f}ms")
    print(f"   Max:     {standard_max:.2f}ms")
    
    if not JIT_AVAILABLE:
        print("\n⚠️  JIT not available for comparison")
        return
    
    # 2. JIT Compiled (first time - includes compilation)
    print("\nCompiling query with JIT...")
    start_compile = time.perf_counter()
    compiled_fn = compile_query(schema._schema, query)
    compilation_time = (time.perf_counter() - start_compile) * 1000
    
    print(f"   Compilation time: {compilation_time:.2f}ms")
    
    # Run compiled version
    print("Running JIT compiled version...")
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        result = compiled_fn(root)
        times.append(time.perf_counter() - start)
    
    jit_avg = statistics.mean(times) * 1000
    jit_min = min(times) * 1000
    jit_max = max(times) * 1000
    
    print(f"✅ JIT Compiled:")
    print(f"   Average: {jit_avg:.2f}ms ({standard_avg/jit_avg:.2f}x faster)")
    print(f"   Min:     {jit_min:.2f}ms")
    print(f"   Max:     {jit_max:.2f}ms")
    
    # 3. JIT with Cache (simulating production)
    print("\nSimulating production with query cache...")
    compiler = CachedJITCompiler(schema._schema, enable_parallel=False)
    
    # Simulate 100 requests of the same query
    times = []
    for i in range(100):
        start = time.perf_counter()
        fn = compiler.compile_query(query)
        result = fn(root)
        times.append(time.perf_counter() - start)
    
    cached_avg = statistics.mean(times) * 1000
    cached_first = times[0] * 1000  # First request (compilation)
    cached_rest_avg = statistics.mean(times[1:]) * 1000  # Subsequent (cached)
    
    stats = compiler.get_cache_stats()
    
    print(f"✅ JIT with Cache (100 requests):")
    print(f"   First request:  {cached_first:.2f}ms (compilation)")
    print(f"   Subsequent avg: {cached_rest_avg:.2f}ms ({standard_avg/cached_rest_avg:.2f}x faster)")
    print(f"   Cache hit rate: {stats.hit_rate:.1%}")
    
    # Summary
    print("\n" + "="*60)
    print("📊 RESULTS SUMMARY")
    print("="*60)
    
    speedup_jit = standard_avg / jit_avg
    speedup_cached = standard_avg / cached_rest_avg
    
    print(f"\n🚀 Performance Improvements:")
    print(f"   JIT Compilation:    {speedup_jit:.2f}x faster")
    print(f"   JIT + Cache:        {speedup_cached:.2f}x faster")
    
    print(f"\n💡 Key Insights:")
    print(f"   • Compilation overhead: {compilation_time:.2f}ms (one-time cost)")
    print(f"   • Break-even point: After {compilation_time//(standard_avg-jit_avg):.0f} requests")
    print(f"   • Cache eliminates compilation overhead completely")
    
    # Show the actual difference in execution
    print(f"\n⏱️  Time Savings per Request:")
    print(f"   JIT:        {standard_avg - jit_avg:.2f}ms saved")
    print(f"   JIT+Cache:  {standard_avg - cached_rest_avg:.2f}ms saved")
    
    requests_per_second_standard = 1000 / standard_avg
    requests_per_second_jit = 1000 / jit_avg
    requests_per_second_cached = 1000 / cached_rest_avg
    
    print(f"\n📈 Throughput (requests/second):")
    print(f"   Standard:   {requests_per_second_standard:.0f} req/s")
    print(f"   JIT:        {requests_per_second_jit:.0f} req/s")
    print(f"   JIT+Cache:  {requests_per_second_cached:.0f} req/s")


if __name__ == "__main__":
    print("\n🎯 JIT Compiler Simple Demonstration")
    print("This example uses synchronous resolvers to clearly show JIT benefits.\n")
    
    run_simple_benchmark()
    
    print("\n✅ Demo complete!")
    print("\n📝 Note: JIT compilation excels with:")
    print("   • Synchronous field resolvers")
    print("   • Complex nested queries")
    print("   • Frequently repeated queries (with caching)")
    print("   • High-throughput APIs")