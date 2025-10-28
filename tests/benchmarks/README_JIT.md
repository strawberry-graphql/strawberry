# JIT Compiler Benchmarks

This directory contains performance benchmarks for the Strawberry JIT compiler using `pytest-codspeed` to track performance over time.

## Overview

The benchmark suite compares JIT-compiled query execution against standard GraphQL execution across various scenarios:

1. **Stadium Benchmark** - Large nested datasets (45k-90k objects)
2. **Simple Queries** - Baseline overhead measurements
3. **Async Parallel** - Concurrent field execution
4. **Compilation** - Cold vs warm cache performance

## Running Benchmarks

### Run All JIT Benchmarks
```bash
pytest tests/benchmarks/test_jit_performance.py --benchmark-only
```

### Run Specific Benchmark
```bash
pytest tests/benchmarks/test_jit_performance.py::test_jit_stadium_vs_standard --benchmark-only
```

### Compare JIT vs Standard
```bash
# Run both to see the difference
pytest tests/benchmarks/test_jit_performance.py::test_jit_stadium_vs_standard \
      tests/benchmarks/test_jit_performance.py::test_standard_stadium_baseline \
      --benchmark-only
```

## Benchmark Details

### 1. Stadium Benchmark (Primary Performance Test)

**Test:** `test_jit_stadium_vs_standard[seats_per_row_250]`
**Baseline:** `test_standard_stadium_baseline[seats_per_row_250]`

```graphql
query StadiumQuery {
  stadium(seatsPerRow: 250) {
    city
    country
    name
    stands {
      sectionType
      seats {    # ~45,000 seats total
        labels   # 5 labels per seat
        x
        y
      }
      priceCategory
      name
    }
  }
}
```

**What it measures:**
- Deeply nested object traversal
- Large result set serialization (~45k objects)
- List field handling
- Memory efficiency

**Expected speedup:** 5-8x faster with JIT

### 2. Parallel Async Execution

**Test:** `test_jit_parallel_async`
**Baseline:** `test_standard_async_baseline`

```graphql
{
  field1  # async, 1ms delay
  field2  # async, 1ms delay
  field3  # async, 1ms delay
  field4  # async, 1ms delay
  field5  # async, 1ms delay
}
```

**What it measures:**
- Parallel execution optimization
- `asyncio.gather()` efficiency
- Concurrent field resolution

**Expected behavior:**
- Standard: ~5ms (sequential)
- JIT: ~1ms (parallel)
- **5x speedup** from parallelization

### 3. Simple Query (Baseline)

**Test:** `test_jit_simple_query`
**Baseline:** `test_standard_simple_query`

```graphql
{
  user(id: 1)
  posts(limit: 10)
}
```

**What it measures:**
- Minimal query overhead
- Function call efficiency
- Basic field resolution

**Expected speedup:** 2-4x faster with JIT

### 4. Compilation Overhead

**Test:** `test_jit_compilation_time`

Measures cold-start compilation time (first request latency).

**Test:** `test_jit_cached_compilation`

Measures cache hit performance (subsequent requests).

**Expected behavior:**
- Cold: 1-5ms compilation time
- Warm: <0.1ms (cache lookup)

### 5. Large Dataset

**Test:** `test_jit_large_dataset[seats_per_row_500]`

Same as stadium benchmark but with 2x data (~90k seats).

**What it measures:**
- Performance scaling with data size
- Memory efficiency at scale

## Performance Tracking

These benchmarks integrate with CodSpeed for continuous performance monitoring:

### On Pull Requests
- Automatically runs on CI
- Comments performance impact
- Catches regressions before merge

### On Main Branch
- Tracks performance trends over time
- Historical comparison available
- Regression alerts

## Interpreting Results

### Good Performance Indicators

✅ **JIT Stadium:** 5-8x faster than baseline
✅ **JIT Async:** ~5x speedup (parallel execution)
✅ **JIT Simple:** 2-4x faster than baseline
✅ **Compilation:** <5ms cold, <0.1ms warm

### Warning Signs

⚠️ **JIT slower than standard** - Likely a bug or regression
⚠️ **Async no speedup** - Parallel execution not working
⚠️ **Compilation >10ms** - Code generation overhead too high
⚠️ **Cache misses** - LRU cache not working properly

## Benchmark Matrix

| Benchmark | JIT | Standard | Speedup | What It Tests |
|-----------|-----|----------|---------|---------------|
| Stadium (250 seats/row) | ✓ | ✓ | 5-8x | Large nested data |
| Stadium (500 seats/row) | ✓ | - | - | Scaling |
| Parallel Async (5 fields) | ✓ | ✓ | 5x | Concurrent execution |
| Simple Query | ✓ | ✓ | 2-4x | Baseline overhead |
| Compilation (cold) | ✓ | - | - | First request |
| Compilation (warm) | ✓ | - | - | Cache performance |

## Adding New Benchmarks

To add a new benchmark:

1. **Create the test function:**
```python
@pytest.mark.benchmark
def test_jit_my_feature(benchmark: BenchmarkFixture):
    schema = strawberry.Schema(query=MyQuery)
    query = "{ myField }"
    compiled_fn = compile_query(schema, query)

    def run():
        return compiled_fn(MyQuery())

    results = benchmark(run)
    assert results["data"] is not None
```

2. **Add baseline comparison:**
```python
@pytest.mark.benchmark
def test_standard_my_feature(benchmark: BenchmarkFixture):
    schema = strawberry.Schema(query=MyQuery)
    query = "{ myField }"

    def run():
        return asyncio.run(schema.execute(query, root_value=MyQuery()))

    results = benchmark(run)
    assert results.errors is None
```

3. **Document expected behavior** in this README

## Best Practices

### DO ✅
- Pre-compile queries before benchmarking (exclude compilation time)
- Use realistic data sizes
- Compare JIT vs standard for same workload
- Add assertions to verify correctness
- Document expected speedup

### DON'T ❌
- Include compilation time in execution benchmarks
- Use trivial queries (not representative)
- Forget the baseline comparison
- Skip result validation
- Mix different workloads

## Troubleshooting

### Benchmarks Failing

```bash
# Run without benchmark flag to see actual errors
pytest tests/benchmarks/test_jit_performance.py -v
```

### Inconsistent Results

```bash
# Run multiple iterations for stability
pytest tests/benchmarks/test_jit_performance.py --benchmark-only --benchmark-autosave
```

### Comparing Branches

```bash
# Save baseline
pytest tests/benchmarks/test_jit_performance.py --benchmark-only --benchmark-save=baseline

# After changes
pytest tests/benchmarks/test_jit_performance.py --benchmark-only --benchmark-compare=baseline
```

## Related Files

- `test_stadium.py` - Original stadium benchmark (standard only)
- `test_jit_performance.py` - JIT vs standard comparisons
- `queries/stadium.graphql` - Stadium query definition

## Future Benchmarks

Potential additions:

- Mutations (serial execution)
- Subscriptions (streaming)
- Interfaces/Unions (type resolution)
- Custom scalars (serialization)
- DataLoader integration
- Real-world API patterns

## References

- [pytest-benchmark docs](https://pytest-benchmark.readthedocs.io/)
- [CodSpeed docs](https://docs.codspeed.io/)
- [JIT compiler docs](../../docs/features/jit-compiler.md)
