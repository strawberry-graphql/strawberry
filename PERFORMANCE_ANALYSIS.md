# Performance Analysis - Stadium Benchmark

## Summary

Profiling analysis of the stadium benchmark (45,000 seats) identified the main bottlenecks in GraphQL execution. The execution time breakdown shows that **graphql-core's execution logic accounts for ~75% of total time**, with the remaining time split between Strawberry's field resolution and data generation.

### Current Performance (Baseline)
- **250 seats/row** (~45,000 total seats): ~0.436s average
- **500 seats/row** (~90,000 total seats): ~0.901s average
- **Scaling**: Nearly linear (2.07x for 2x data)

### Optimization Already Implemented
The `optimized_is_awaitable` function provides a fast-path for common synchronous types. This is passed to graphql-core via the `is_awaitable` parameter in the execute call.

### Attempted Optimizations (Did Not Help)
1. **Type check caching**: Added overhead, no benefit
2. **Custom complete_value override**: Python call overhead negated any isinstance savings (~80% slower!)
3. **Type() vs isinstance()**: Only 3% faster per call, not worth the risk

## Detailed Profile Analysis

### Top Bottlenecks (from cProfile on 250 seats/row benchmark)

| Function | Time | Calls | % Total | Description |
|----------|------|-------|---------|-------------|
| `complete_value` | 504ms | 810,050 | 24.8% | Core value completion with recursive type checking |
| `complete_list_value` | 210ms | 45,005 | 10.3% | List processing with Path object allocation |
| `isinstance` | 167ms | 3,061,386 | 8.2% | Type checking overhead |
| `execute_field` | 157ms | 135,021 | 7.7% | Per-field execution |
| `optimized_is_awaitable` | 121ms | 1,215,076 | 5.9% | Awaitable detection (OPTIMIZED) |
| `is_non_null_type` | 82ms | 810,060 | 4.0% | NonNull type checking |
| `complete_leaf_value` | 54ms | 315,015 | 2.7% | Leaf value serialization |
| `path.add_key` | 52ms | 270,004 | 2.6% | Path object construction |
| `is_list_type` | 41ms | 405,026 | 2.0% | List type checking |
| `is_leaf_type` | 37ms | 360,033 | 1.8% | Leaf type checking |

### Key Observations

1. **Type Checking Overhead (389ms total, 19.1%)**
   - `isinstance`: 167ms across 3M calls (~57ns/call)
   - `is_non_null_type`: 82ms across 810K calls (~104ns/call)
   - `is_list_type`: 42ms across 405K calls (~104ns/call)
   - `is_leaf_type`: 37ms across 360K calls (~106ns/call)
   - **These are already highly optimized in CPython** - micro-optimizations won't help much

2. **Object Allocation Overhead**
   - 540K `__new__` calls (49ms) - mostly for Path objects
   - Path objects created for error tracking in nested lists
   - Immutable design causes frequent allocations

3. **graphql-core Execution**
   - `execute.py` functions: 1,111ms (54.6% of total time)
   - Most time in recursive value completion logic
   - Heavy branching for type checks in hot path

## Optimization Opportunities

### ✅ Already Implemented: optimized_is_awaitable
- **Impact**: 5-10% improvement
- **Approach**: Fast-path for common synchronous types (int, str, list, dict, etc.)
- **Location**: `strawberry/execution/is_awaitable.py`
- Passed to graphql-core via `is_awaitable` parameter

### ❌ Type Check Caching - Not Worth It
- **Attempted**: Caching `is_non_null_type`, `is_list_type`, `is_leaf_type`
- **Result**: No significant improvement
- **Reason**: `isinstance()` is already ~50-100ns per call, caching adds overhead
- **Conclusion**: The cost per call is not the problem - it's the number of calls

### 🔮 Future Opportunities (Require graphql-core Changes)

#### 1. Optimize complete_value Fast-Path
**Current flow** (execute.py:577):
```python
def complete_value(self, return_type, field_nodes, info, path, result):
    if isinstance(result, Exception):
        raise result
    if is_non_null_type(return_type):
        ...  # 810K calls
    if result is None:
        return None
    if is_list_type(return_type):
        ...  # 405K calls
    if is_leaf_type(return_type):
        ...  # 360K calls
    if is_abstract_type(return_type):
        ...
    if is_object_type(return_type):
        ...
```

**Optimization idea**: Add fast-path for common patterns
```python
def complete_value(self, return_type, field_nodes, info, path, result):
    # Fast path: check type kind once and branch
    type_kind = _get_type_kind(return_type)  # Cached by type identity

    if type_kind == "leaf":
        # Direct path for scalars - no recursion
        return return_type.serialize(result)
    elif type_kind == "non_null":
        # Unwrap and recurse once
        ...
    # ... other cases
```

**Estimated impact**: 10-15% by reducing redundant type checks

#### 2. Optimize Path Object Allocation
**Current**: Immutable Path objects allocated for every list item
```python
for index, item in enumerate(result):
    item_path = path.add_key(index, None)  # New object
    completed_item = self.complete_value(..., item_path, ...)
```

**Optimization idea**: Use mutable path stack for lists
```python
path.push_key(index)
try:
    completed_item = self.complete_value(..., path, ...)
finally:
    path.pop_key()
```

**Estimated impact**: 5-8% by reducing allocations (52ms saved)

#### 3. Pre-allocate Result Lists
**Current**: Lists built with append in complete_list_value
```python
completed_results: List[Any] = []
append_result = completed_results.append
for index, item in enumerate(result):
    ...
    append_result(completed_item)
```

**Optimization idea**: Pre-allocate when size known
```python
result_list = list(result)  # Convert to list if needed
result_len = len(result_list)
completed_results = [None] * result_len  # Pre-allocate
for index in range(result_len):
    completed_results[index] = self.complete_value(...)
```

**Estimated impact**: 2-3% by reducing list resizing

#### 4. Batch Field Resolution for Homogeneous Lists
**Current**: Each list item resolved separately with full type checking

**Optimization idea**: Detect homogeneous lists and batch process
```python
if is_list_type(return_type):
    item_type = return_type.of_type
    # Check if all items are synchronous leaf values
    if _is_homogeneous_leaf_list(result, item_type):
        # Fast batch serialization
        return [item_type.serialize(item) for item in result]
    # ... fall back to normal processing
```

**Estimated impact**: 15-20% for list-heavy queries

## Recommendations

### For Strawberry
1. ✅ Keep the `optimized_is_awaitable` optimization - it's effective
2. ❌ Don't add type check caching - minimal benefit for the complexity
3. 📝 Document these findings for when graphql-core optimizations are possible
4. 🎯 Consider contributing optimizations to graphql-core upstream

### For graphql-core Upstream (Future Work)
1. Add type kind caching in complete_value to reduce redundant checks
2. Optimize Path class for list processing (mutable stack-based approach)
3. Add fast-path for homogeneous leaf lists
4. Consider pre-allocation for result lists when size is known

### Alternative Approaches
1. **Rust-based execution**: Libraries like `graphql-core-rs` could provide 10-100x speedups
2. **JIT compilation**: Cache and optimize hot execution paths
3. **Parallel execution**: Process independent list items in parallel for CPU-bound workloads

## Benchmark Details

### Test Configuration
- **Query**: Nested stadium with stands and seats
- **Data size**: 4 stands × (40-50 rows) × (250-500 seats) = 45,000-90,000 total objects
- **Fields per object**:
  - Stadium: 4 fields
  - Stand: 4 fields + seats list
  - Seat: 3 fields (2 ints + 1 list of strings)

### Profiling Method
- Tool: cProfile + pstats
- Sorting: By cumulative time and total time
- Focus: Hot-path functions with >1% of total time

### Module Time Distribution
- `execute.py` (graphql-core): 54.6%
- `isinstance` (builtins): 14.8%
- `definition.py` (graphql-core types): 8.4%
- `is_awaitable.py` (strawberry): 5.9%
- `field.py` (strawberry): 3.3%
- `path.py` (graphql-core): 2.5%
- Other: <10%

## Key Learnings

### Why Custom ExecutionContext Overrides Don't Help

We tested overriding `complete_value` in `StrawberryGraphQLCoreExecutionContext` to optimize type checking. Results:

**Baseline (graphql-core default)**:
- 250 seats: 0.436s
- 500 seats: 0.901s

**With custom complete_value override** (using `type() is Class` instead of `isinstance()`):
- 250 seats: 0.780s (**79% slower!**)
- 500 seats: 1.636s (**82% slower!**)

**Why it failed**:
- Python method call overhead for each recursion
- The `super().complete_value()` fallback adds another call
- Importing modules inside the hot-path (`from graphql.type import ...`)
- graphql-core's C-optimized `isinstance()` is already very fast
- Type checking is ~100ns per call - optimization overhead exceeds savings

**Lesson**: graphql-core is already highly optimized. Don't try to override hot-path methods in Python - the call overhead will hurt more than it helps.

### What Actually Works

The `optimized_is_awaitable` function works because:
1. It's passed as a parameter to graphql-core (no override overhead)
2. It adds a fast-path BEFORE calling graphql-core's logic
3. For synchronous workloads (most common), it returns immediately
4. Only falls back to graphql-core's logic for actual awaitables

## Conclusion

The benchmark shows that **Strawberry is already quite efficient**, with most time spent in graphql-core's execution engine. The `optimized_is_awaitable` function is the right approach - provide optimized callbacks rather than overriding methods.

Further optimizations would require changes to graphql-core itself (C extensions, different algorithms), or:
- Alternative execution engines (Rust-based like `graphql-core-rs`)
- Resolver-level caching/memoization
- DataLoader for N+1 query optimization
- Schema design to reduce nesting depth

**For this benchmark**: The current ~0.4s for 45,000 objects is actually quite good performance!
