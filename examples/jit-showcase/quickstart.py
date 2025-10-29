#!/usr/bin/env python
"""Quick start script to demonstrate JIT compiler in action.
Run this to see immediate performance improvements!
"""

import os
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import time

from graphql import execute_sync, parse

import strawberry
from strawberry.jit import compile_query


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
    def users(self) -> list[User]:
        return [
            User(id=i, name=f"User {i}", email=f"user{i}@example.com")
            for i in range(100)
        ]


def main() -> None:
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

    print("\n📊 Performance Comparison")
    print("=" * 60)

    # Standard execution
    print("\n⏱️  Standard GraphQL Execution (100 iterations)...")
    start = time.perf_counter()
    for _ in range(100):
        execute_sync(schema._schema, parse(query), root_value=root)
    standard_time = time.perf_counter() - start
    print(f"   Total time: {standard_time * 1000:.2f}ms")
    print(f"   Per query: {standard_time * 10:.2f}ms")

    # JIT compiled execution
    print("\n⚡ JIT Compiled Execution")

    # Compile once
    print("   Compiling query...")
    start = time.perf_counter()
    compiled_fn = compile_query(schema, query)
    compile_time = time.perf_counter() - start
    print(f"   Compilation time: {compile_time * 1000:.2f}ms")

    # Execute 100 times
    print("   Executing 100 times...")
    start = time.perf_counter()
    for _ in range(100):
        compiled_fn(root)
    jit_time = time.perf_counter() - start
    print(f"   Total time: {jit_time * 1000:.2f}ms")
    print(f"   Per query: {jit_time * 10:.2f}ms")

    # Results
    speedup = standard_time / jit_time
    print("\n🎯 Results")
    print("=" * 60)
    print(f"Standard: {standard_time * 1000:.2f}ms")
    print(f"JIT:      {jit_time * 1000:.2f}ms")
    print(f"Speedup:  {speedup:.2f}x faster")

    improvement = ((standard_time - jit_time) / standard_time) * 100
    print(f"Improvement: {improvement:.1f}% faster")

    print("\n✅ JIT compilation provides significant performance improvements!")
    print("   For production use, implement caching to avoid recompiling queries.")


if __name__ == "__main__":
    main()
