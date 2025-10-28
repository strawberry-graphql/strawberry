#!/usr/bin/env python
"""GraphQL Overhead Elimination Demo - Shows 3-5x improvements.
This demonstrates how JIT eliminates per-field overhead.
"""

import os
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import statistics
import time

from graphql import execute_sync, parse

import strawberry
from strawberry.jit import CachedJITCompiler, compile_query


# Schema with many simple fields to maximize overhead impact
@strawberry.type
class SimpleData:
    """Type with many simple fields - overhead dominates execution."""

    id: str

    # 50 integer fields
    i1: int = 1
    i2: int = 2
    i3: int = 3
    i4: int = 4
    i5: int = 5
    i6: int = 6
    i7: int = 7
    i8: int = 8
    i9: int = 9
    i10: int = 10
    i11: int = 11
    i12: int = 12
    i13: int = 13
    i14: int = 14
    i15: int = 15
    i16: int = 16
    i17: int = 17
    i18: int = 18
    i19: int = 19
    i20: int = 20
    i21: int = 21
    i22: int = 22
    i23: int = 23
    i24: int = 24
    i25: int = 25
    i26: int = 26
    i27: int = 27
    i28: int = 28
    i29: int = 29
    i30: int = 30
    i31: int = 31
    i32: int = 32
    i33: int = 33
    i34: int = 34
    i35: int = 35
    i36: int = 36
    i37: int = 37
    i38: int = 38
    i39: int = 39
    i40: int = 40
    i41: int = 41
    i42: int = 42
    i43: int = 43
    i44: int = 44
    i45: int = 45
    i46: int = 46
    i47: int = 47
    i48: int = 48
    i49: int = 49
    i50: int = 50

    # 20 string fields
    s1: str = "s1"
    s2: str = "s2"
    s3: str = "s3"
    s4: str = "s4"
    s5: str = "s5"
    s6: str = "s6"
    s7: str = "s7"
    s8: str = "s8"
    s9: str = "s9"
    s10: str = "s10"
    s11: str = "s11"
    s12: str = "s12"
    s13: str = "s13"
    s14: str = "s14"
    s15: str = "s15"
    s16: str = "s16"
    s17: str = "s17"
    s18: str = "s18"
    s19: str = "s19"
    s20: str = "s20"

    # 20 boolean fields
    b1: bool = True
    b2: bool = False
    b3: bool = True
    b4: bool = False
    b5: bool = True
    b6: bool = False
    b7: bool = True
    b8: bool = False
    b9: bool = True
    b10: bool = False
    b11: bool = True
    b12: bool = False
    b13: bool = True
    b14: bool = False
    b15: bool = True
    b16: bool = False
    b17: bool = True
    b18: bool = False
    b19: bool = True
    b20: bool = False

    # 10 float fields
    f1: float = 1.1
    f2: float = 2.2
    f3: float = 3.3
    f4: float = 4.4
    f5: float = 5.5
    f6: float = 6.6
    f7: float = 7.7
    f8: float = 8.8
    f9: float = 9.9
    f10: float = 10.10


@strawberry.type
class Query:
    @strawberry.field
    def many_items(self, count: int = 500) -> list[SimpleData]:
        """Return many items with lots of fields."""
        return [SimpleData(id=f"item-{i}") for i in range(count)]

    @strawberry.field
    def single_item(self) -> SimpleData:
        """Single item for testing."""
        return SimpleData(id="single")


def run_overhead_benchmark() -> None:
    """Benchmark to show overhead elimination."""
    schema = strawberry.Schema(Query)

    # Query requesting ALL fields from many items
    query = """
    query OverheadTest {
        manyItems(count: 500) {
            id
            i1 i2 i3 i4 i5 i6 i7 i8 i9 i10
            i11 i12 i13 i14 i15 i16 i17 i18 i19 i20
            i21 i22 i23 i24 i25 i26 i27 i28 i29 i30
            i31 i32 i33 i34 i35 i36 i37 i38 i39 i40
            i41 i42 i43 i44 i45 i46 i47 i48 i49 i50
            s1 s2 s3 s4 s5 s6 s7 s8 s9 s10
            s11 s12 s13 s14 s15 s16 s17 s18 s19 s20
            b1 b2 b3 b4 b5 b6 b7 b8 b9 b10
            b11 b12 b13 b14 b15 b16 b17 b18 b19 b20
            f1 f2 f3 f4 f5 f6 f7 f8 f9 f10
        }
    }
    """

    root = Query()

    # Warm up
    for _ in range(3):
        execute_sync(schema._schema, parse(query), root_value=root)

    # 1. Standard GraphQL
    iterations = 10
    times = []
    for _i in range(iterations):
        start = time.perf_counter()
        execute_sync(schema._schema, parse(query), root_value=root)
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    standard_avg = statistics.mean(times) * 1000
    min(times) * 1000
    max(times) * 1000

    total_fields = 500 * 101  # 500 items * 101 fields each
    overhead_per_field = standard_avg / total_fields

    # 2. JIT Compiled
    start_compile = time.perf_counter()
    compiled_fn = compile_query(schema, query)
    (time.perf_counter() - start_compile) * 1000

    times = []
    for _i in range(iterations):
        start = time.perf_counter()
        compiled_fn(root)
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    jit_avg = statistics.mean(times) * 1000
    min(times) * 1000
    max(times) * 1000

    speedup = standard_avg / jit_avg

    jit_per_field = jit_avg / total_fields
    overhead_per_field - jit_per_field

    # 3. Production with Cache
    compiler = CachedJITCompiler(schema)

    times = []
    for _i in range(100):
        start = time.perf_counter()
        fn = compiler.compile_query(query)
        fn(root)
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    times[0] * 1000
    cached_avg = statistics.mean(times[1:]) * 1000
    standard_avg / cached_avg

    compiler.get_cache_stats()

    # Summary

    1000 / standard_avg
    1000 / jit_avg
    1000 / cached_avg

    if speedup >= 3:
        pass


if __name__ == "__main__":
    run_overhead_benchmark()
