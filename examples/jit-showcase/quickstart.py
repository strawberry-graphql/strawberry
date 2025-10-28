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
from strawberry.jit import CachedJITCompiler, compile_query


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

    # Standard execution
    start = time.perf_counter()
    for _ in range(100):
        execute_sync(schema._schema, parse(query), root_value=root)
    standard_time = time.perf_counter() - start

    # JIT compiled execution

    # Compile once
    start = time.perf_counter()
    compiled_fn = compile_query(schema, query)
    time.perf_counter() - start

    # Execute 100 times
    start = time.perf_counter()
    for _ in range(100):
        compiled_fn(root)
    jit_time = time.perf_counter() - start

    # Results
    standard_time / jit_time

    # 3. JIT with Cache
    compiler = CachedJITCompiler(schema)

    # Simulate production usage
    cache_times = []
    for _i in range(100):
        start = time.perf_counter()
        fn = compiler.compile_query(query)
        fn(root)
        cache_times.append(time.perf_counter() - start)

    cache_times[0] * 1000
    cached_avg = sum(cache_times[1:]) * 1000 / 99  # Average of cached requests
    (standard_time * 10) / cached_avg

    compiler.get_cache_stats()


if __name__ == "__main__":
    main()
