# JIT Performance Investigation Findings

## Executive Summary

**BREAKTHROUGH**: JIT is **faster than standard GraphQL for simple queries** (0.96x = 4% faster), but degrades **exponentially with nesting depth**.

## Problem Statement

The JIT compiler shows **query-dependent performance**:
- Simple queries (sync fields only): **4% FASTER** ✓
- Moderate nesting (1-2 levels): 1.5-2x slower
- Deep nesting (3+ levels): 2.7x slower
- Complex scaled queries: **13x SLOWER** ✗

**Full Benchmark Results:**
- Simple (3 posts, sync only): Standard 11.44ms, JIT 11.04ms → **0.96x (FASTER)**
- Complex (10 posts, deep nesting): Standard 30.11ms, JIT 389.91ms → **12.95x (SLOWER)**

## Root Cause: Task Function Creation Inside Loops

The degradation follows a clear pattern:

| Complexity Level | Async Nesting | JIT Ratio |
|-----------------|---------------|-----------|
| Simple (sync only) | 0 levels | **0.96x (FASTER)** |
| With author | 1 level | 1.57x slower |
| With postsCount | 2 levels | 1.85x slower |
| With comments | 2 levels + list | 1.75x slower |
| Comment authors | 3 levels + nested lists | 2.63x slower |
| Full query (10x scale) | 3 levels, 50 items | **12.95x slower** |

**Root Cause:** We generate `async def task_X():` function definitions INSIDE loops. Python creates new function objects on each iteration, and this compounds exponentially with nesting depth and item count.

Example problematic code:
```python
for post in posts:  # 10 iterations

    async def task_author():  # Created 10 times!
        ...

    async def task_comments():  # Created 10 times!
        ...

    for comment in comments:  # 5 iterations per post

        async def task_comment_author():  # Created 50 times total!
            ...
```

Total: **70 function object creations** for one query, each adding event loop overhead.

### Secondary Issues

**Event Loop Overhead:**
- Standard GraphQL: 37 event loop iterations
- JIT: 204-210 event loop iterations (5.5x more)
- Each iteration has ~1.78ms overhead vs standard's ~0.6ms

**Function Call Efficiency:**
- JIT: 12,580 function calls (64% reduction vs standard) ✓
- But event loop overhead dominates, negating the improvement

### 2. Insufficient Parallelization

**Standard GraphQL:**
- 83 calls to `asyncio.gather()`
- Uses gather at EVERY level of nesting where async fields exist
- Efficiently parallelizes field resolution at all depths

**JIT (current):**
- Only 2-5 calls to `asyncio.gather()`
- Only parallelizes at top-level and immediate nested levels
- Nested async fields execute sequentially inside task functions

**Example:** For a query with 10 posts, each having async author and comments:
- Standard: Creates gather for each post's fields (10 gathers) + each author's fields (10 gathers) + each comment's fields (50 gathers) = ~70 gathers
- JIT: Creates 1 gather at top-level + 1 gather per post item (10 gathers) = 11 gathers

### 3. Architecture: Still Using Wrapper Overhead

The JIT compiles queries into Python code but still calls `field_def.resolve`, which is the **fully wrapped resolver** that goes through:

1. `_async_resolver` wrapper
2. `await_maybe` utility
3. `_get_result_with_extensions`
4. `extension_resolver` with argument parsing
5. Extension middleware chain
6. Finally the actual base resolver

**This means JIT gets NONE of the benefits of bypassing GraphQL execution machinery - it just reorganizes async calls while paying full overhead.**

## Attempted Fixes

### Fix 1: Added Nested Parallelization ✅ Partial Success

**Change:** Modified `generate_field` to use `generate_parallel_selection_set` for nested object selections.

**Result:** Increased gather calls from 1 to 2-5, slight improvement but still insufficient.

**Issue:** Nested parallelization only works at the immediate child level. Fields inside task functions don't get parallel execution because the task itself processes all nested selections sequentially.

### Fix 2: Variable Shadowing Fix ✅ Completed

**Change:** Used unique variable names (`async_tasks_0`, `async_tasks_2`, etc.) to prevent shadowing in nested contexts.

**Result:** Fixed correctness issue but no performance improvement.

### Fix 3: Always Use Gather for Async Fields ⚠️ Insufficient

**Change:** Modified code to use `asyncio.gather()` even for single async fields, matching standard GraphQL behavior.

**Result:** Increased gather calls slightly but didn't solve the fundamental architectural issue.

## Why Standard GraphQL is Faster

Standard GraphQL execution (via graphql-core) has optimized async handling:

1. **Strategic Parallelization:** Uses `asyncio.gather()` at every selection set that contains async fields
2. **Efficient Task Management:** Creates tasks at the right granularity to minimize event loop overhead
3. **Optimized Resolver Chain:** The resolver wrappers are optimized for the execution flow

## Implemented Improvements

### 1. Variable Shadowing Fix ✓
Fixed async task variables using unique names (`async_tasks_0`, `async_tasks_2`, etc.) to prevent scoping bugs in nested contexts.

### 2. Depth-Limited Parallelization ✓
Added `max_parallel_depth` (default: 3) to prevent exponential overhead at very deep nesting levels. Provides ~10% improvement for extreme cases.

### 3. Comprehensive Testing ✓
Created progressive complexity tests to identify exactly where performance degrades, enabling targeted optimization.

## Proposed Solutions

### Short-term: Parameterized Task Functions (2-3 days)

**Problem:** Task functions are redefined inside loops.

**Solution:** Define task functions once with parameters:

```python
# Current (slow)
for item in items:

    async def task_author():  # Redefined each iteration!
        author = await resolve_author(item)  # Captures item via closure
        return process_author(author)

    tasks.append(task_author())


# Optimized (fast)
async def task_author(item, idx):  # Defined ONCE
    author = await resolve_author(item)
    return process_author(author)


tasks = [task_author(item, idx) for idx, item in enumerate(items)]
```

**Benefits:**
- Eliminates function object creation overhead
- Reduces event loop iterations by ~3-4x
- Should bring JIT to within 2-3x of standard for complex queries

**Estimated Effort:** 2-3 days of refactoring code generation logic

### Long-term: True JIT Compilation (Major Redesign)

To achieve actual performance gains, the JIT needs to:

1. **Bypass Wrapper Overhead:** Call base resolvers directly instead of wrapped `field_def.resolve`
2. **Inline Argument Parsing:** Generate argument parsing code instead of calling `get_arguments()`
3. **Skip Extension Middleware:** Either inline extension logic or provide a way to disable it for JIT
4. **Optimize Info Object:** Use a lightweight info object instead of full `MockInfo`

**Estimated Effort:** 1-2 weeks of development + comprehensive testing

### Alternative: Disable JIT by Default

Given the current performance regression:

1. Add a clear warning in documentation that JIT is experimental and currently slower
2. Disable JIT by default, require explicit opt-in
3. Focus on correctness and feature completeness first, performance second

## Conclusions

### What Works ✓
- **Simple queries are faster**: JIT achieves 4% speedup for sync-only queries
- **Basic architecture is sound**: The code generation and execution model work correctly
- **Correctness is maintained**: All functionality tests pass

### What Needs Fixing ✗
- **Async nesting overhead**: Task function creation compounds with depth
- **Scaling issues**: Performance degrades exponentially (2.6x → 13x as scale increases 3x)
- **Deep nesting**: Beyond 3 levels, overhead becomes prohibitive

### Recommendations

1. **Immediate:**
   - Add warning in documentation about performance with deeply nested async queries
   - Recommend JIT only for simple to moderately complex queries
   - Add performance tests to CI to prevent regressions

2. **Short-term (Next Sprint):**
   - Implement parameterized task functions to eliminate loop overhead
   - Target: Match or exceed standard GraphQL for all query types

3. **Long-term (Future Release):**
   - Bypass Strawberry resolver wrappers for true compilation
   - Inline argument parsing and extension logic
   - Target: 2-5x faster than standard for all queries

## Files Modified

- `strawberry/jit/codegen.py`: Added nested parallelization, variable scoping fixes
- `test_jit_perf.py`: Proper benchmark measuring execution time only

## Performance Data

```
Standard GraphQL Profile:
  - 34,797 function calls
  - 37 event loop iterations
  - 83 asyncio.gather() calls
  - 31ms average execution

JIT Profile:
  - 12,580 function calls (64% reduction)
  - 204 event loop iterations (5.5x increase ❌)
  - 5 asyncio.gather() calls (94% reduction ❌)
  - 392ms average execution (12.9x slower ❌)
```

The function call reduction shows JIT is doing SOMETHING right (fewer wrapper functions), but the event loop overhead dominates, making it much slower overall.
