#!/usr/bin/env python
"""
Quick start script to demonstrate JIT compiler in action.
Run this to see immediate performance improvements!
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from typing import List
import strawberry
from graphql import execute_sync, parse
import time

# Try importing JIT
try:
    from strawberry.jit_compiler import compile_query
    from strawberry.jit_compiler_cached import CachedJITCompiler
    JIT_AVAILABLE = True
except ImportError:
    JIT_AVAILABLE = False
    print("⚠️  JIT compiler not available")


# Simple schema
@strawberry.type
class User:
    id: int
    name: str
    email: str
    
    @strawberry.field
    def display_name(self) -> str:
        return f"{self.name} ({self.email})"


@strawberry.type  
class Query:
    @strawberry.field
    def users(self) -> List[User]:
        return [
            User(id=i, name=f"User {i}", email=f"user{i}@example.com")
            for i in range(100)
        ]


def main():
    print("\n" + "="*60)
    print("⚡ STRAWBERRY JIT COMPILER - QUICK START")
    print("="*60)
    
    schema = strawberry.Schema(Query)
    
    query = """
    query GetUsers {
        users {
            id
            name
            email
            displayName
        }
    }
    """
    
    root = Query()
    
    print("\nQuery: Fetching 100 users with computed displayName field\n")
    
    # Standard execution
    print("1️⃣  Standard GraphQL Execution:")
    start = time.perf_counter()
    for _ in range(100):
        result = execute_sync(schema._schema, parse(query), root_value=root)
    standard_time = time.perf_counter() - start
    print(f"   Time for 100 executions: {standard_time*1000:.2f}ms")
    print(f"   Average per request:     {standard_time*10:.2f}ms")
    
    if JIT_AVAILABLE:
        # JIT compiled execution
        print("\n2️⃣  JIT Compiled Execution:")
        
        # Compile once
        start = time.perf_counter()
        compiled_fn = compile_query(schema._schema, query)
        compile_time = time.perf_counter() - start
        print(f"   Compilation time:        {compile_time*1000:.2f}ms (one-time)")
        
        # Execute 100 times
        start = time.perf_counter()
        for _ in range(100):
            result = compiled_fn(root)
        jit_time = time.perf_counter() - start
        print(f"   Time for 100 executions: {jit_time*1000:.2f}ms")
        print(f"   Average per request:     {jit_time*10:.2f}ms")
        
        # Results
        speedup = standard_time / jit_time
        print(f"\n🚀 Results:")
        print(f"   JIT is {speedup:.2f}x faster!")
        print(f"   Time saved: {(standard_time - jit_time)*1000:.2f}ms")
        print(f"   Break-even after {compile_time/(standard_time/100 - jit_time/100):.0f} requests")
        
        # 3. JIT with Cache
        print("\n3️⃣  JIT with Cache (Production Mode):")
        compiler = CachedJITCompiler(schema._schema, enable_parallel=False)
        
        # Simulate production usage
        print("   Simulating 100 requests...")
        cache_times = []
        for i in range(100):
            start = time.perf_counter()
            fn = compiler.compile_query(query)
            result = fn(root)
            cache_times.append(time.perf_counter() - start)
        
        first_time = cache_times[0] * 1000
        cached_avg = sum(cache_times[1:]) * 1000 / 99  # Average of cached requests
        cache_speedup = (standard_time * 10) / cached_avg
        
        stats = compiler.get_cache_stats()
        
        print(f"   First request:           {first_time:.2f}ms (includes compilation)")
        print(f"   Cached requests (avg):   {cached_avg:.2f}ms")
        print(f"   Cache speedup:           {cache_speedup:.2f}x faster")
        print(f"   Cache hit rate:          {stats.hit_rate:.1%}")
    
    print("\n" + "="*60)
    print("✅ Quick start complete!")
    print("\n📝 Next steps:")
    print("   1. Run 'python simple_demo.py' for detailed benchmarks")
    print("   2. Run 'python server.py' to start the GraphQL server")
    print("   3. Run 'python benchmark.py' for comprehensive tests")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()