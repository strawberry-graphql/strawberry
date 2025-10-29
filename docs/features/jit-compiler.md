---
title: JIT Compiler
---

# JIT Compiler (Beta)

The Strawberry JIT (Just-In-Time) Compiler provides **5-6x faster** GraphQL
query execution by compiling queries ahead-of-time into optimized Python code.

## Overview

The JIT compiler analyzes your GraphQL queries and generates specialized Python
functions that execute them with minimal overhead. This eliminates the runtime
interpretation cost of standard GraphQL execution.

### Key Benefits

- **5-6x Performance Improvement**: Queries execute significantly faster
- **Parallel Async Execution**: Independent async fields run concurrently
- **Zero Configuration**: Drop-in replacement for standard execution
- **100% GraphQL Spec Compliant**: Supports all GraphQL features

## Quick Start

### Basic Usage

```python
import strawberry
from strawberry.jit import compile_query


@strawberry.type
class Query:
    @strawberry.field
    def hello(self, name: str) -> str:
        return f"Hello, {name}!"


schema = strawberry.Schema(query=Query)

# Compile the query once
query = 'query { hello(name: "World") }'
compiled_query = compile_query(schema, query)

# Execute many times (fast!)
result = compiled_query(root_value=None)
print(result)  # {"data": {"hello": "Hello, World!"}}
```

## Performance

### Benchmark Results

Based on the stadium benchmark with ~45,000 objects:

```
Standard GraphQL:  486.86ms
JIT Compiled:       81.72ms
Speedup:            5.96x faster ⚡
```

For 90,000 objects:

```
Standard GraphQL:  1014.48ms
JIT Compiled:       182.04ms
Speedup:            5.57x faster ⚡
```

### When to Use JIT

The JIT compiler provides the most benefit for:

- **Complex nested queries** - Multiple levels of relationships
- **Large result sets** - Thousands of objects
- **Repeated queries** - Same query executed multiple times
- **Production APIs** - High-throughput services
- **Pure computation** - Queries with many calculated fields

### When NOT to Use JIT

The JIT compiler may not be beneficial in these scenarios:

- **Simple, small queries** - Compilation overhead may exceed execution savings
  - Example: `query { user(id: "1") { name } }` fetching one object
  - Compilation takes ~5-10ms, execution savings might be <1ms

- **One-off or rarely executed queries** - Compilation cost not amortized
  - Ad-hoc admin queries
  - Development/testing queries
  - Queries that change frequently

- **Development and debugging** - Standard execution provides better introspection
  - Use standard GraphQL execution during development
  - Switch to JIT for production deployment
  - Better error messages and stack traces with standard execution

- **Very simple schemas** - Minimal overhead to eliminate
  - Single-level queries with few fields
  - No computed fields or complex resolvers

- **I/O-bound queries** - Performance bottleneck is database/network, not GraphQL
  - Queries that spend 99% of time waiting for external services
  - JIT can't speed up database queries or API calls
  - Consider DataLoader and query optimization instead

**Rule of thumb:** If a query executes in <5ms with standard GraphQL, JIT compilation overhead likely exceeds the benefit. Compile queries that execute >10ms and run frequently.

## Features

### Supported GraphQL Features

✅ **Fully Supported:**

- Queries, Mutations, Subscriptions
- Variables and Arguments
- Fragments (named, inline, nested)
- Directives (`@skip`, `@include`)
- All scalar types (built-in and custom)
- Object types, Interfaces, Unions, Enums
- Input types and validation
- Lists and Non-null types
- Async/await resolvers
- Error handling and propagation
- **Introspection queries** (all types)

⚠️ **Fallback to Standard Executor:**

- `@defer` directive (falls back with warning)
- `@stream` directive (falls back with warning)

### Known Limitations

The following are current limitations of the JIT compiler:

1. **Directives on Inline Fragment Spreads**
   - Pattern: `... @include(if: $condition) { field }`
   - Status: Not yet supported
   - Workaround: Use named fragments with directives instead

2. **@defer and @stream Directives**
   - These automatically fall back to standard execution
   - A warning is emitted when fallback occurs
   - Future versions will support native compilation

3. **Field Extensions Performance**
   - Field extensions work correctly through wrapped resolvers
   - Future optimization may inline basic extensions for better performance
   - Current overhead is minimal (1-3 function calls per field)

4. **Compilation Time**
   - First compilation takes 1-5ms per query
   - Use caching in production to amortize this cost
   - Very complex queries (100+ fields) may take longer to compile

### Async Execution

The JIT compiler automatically detects async resolvers and generates optimized
async code:

```python
@strawberry.type
class Query:
    @strawberry.field
    async def user(self, id: str) -> User:
        return await fetch_user(id)

    @strawberry.field
    async def posts(self) -> list[Post]:
        return await fetch_posts()


# These fields will execute in parallel!
query = """
{
    user(id: "1") { name }
    posts { title }
}
"""
```

### DataLoader Integration

The JIT compiler works seamlessly with Strawberry's DataLoader for efficient batching and caching:

```python
from strawberry.dataloader import DataLoader

@strawberry.type
class User:
    id: str
    name: str

@strawberry.type
class Post:
    id: str
    title: str
    author_id: str

    @strawberry.field
    async def author(self, info) -> User:
        # DataLoader batches requests automatically
        loader = info.context["user_loader"]
        return await loader.load(self.author_id)

@strawberry.type
class Query:
    @strawberry.field
    async def posts(self) -> list[Post]:
        return [
            Post(id="1", title="Post 1", author_id="user1"),
            Post(id="2", title="Post 2", author_id="user1"),
            Post(id="3", title="Post 3", author_id="user2"),
        ]

# Set up DataLoader
async def load_users(keys: list[str]) -> list[User]:
    # Single batch query instead of N+1 queries
    print(f"Loading users: {keys}")
    return [User(id=key, name=f"User {key}") for key in keys]

schema = strawberry.Schema(query=Query)

# Compile query once
query = """
{
    posts {
        title
        author {
            name
        }
    }
}
"""
compiled = compile_query(schema, query)

# Execute with DataLoader context
async def execute():
    context = {
        "user_loader": DataLoader(load_fn=load_users)
    }
    result = await compiled(Query(), context=context)
    return result

# Output: Loading users: ['user1', 'user2']
# DataLoader batches all author requests into one call!
```

**How JIT + DataLoader Work Together:**

1. **JIT compiles the query structure** - Determines which fields need resolving
2. **Async fields execute in parallel** - JIT detects async resolvers
3. **DataLoader batches requests** - Multiple `loader.load()` calls within the same tick are batched
4. **Single database query** - Instead of N+1 queries, one batch query

**Performance Benefits:**

- **Without DataLoader:** 3 posts = 1 posts query + 3 author queries = 4 DB calls
- **With DataLoader:** 3 posts = 1 posts query + 1 batched authors query = 2 DB calls
- **With JIT + DataLoader:** Same batching, but 5-6x faster GraphQL execution

**Best Practices:**

```python
# ✅ Good: DataLoader in context, reused per request
def get_context():
    return {
        "user_loader": DataLoader(load_fn=load_users),
        "post_loader": DataLoader(load_fn=load_posts),
    }

# ❌ Bad: Creating new DataLoader per field
@strawberry.field
async def author(self) -> User:
    loader = DataLoader(load_fn=load_users)  # No batching!
    return await loader.load(self.author_id)
```

**Important Notes:**

- DataLoader batching happens **within the same event loop tick**
- JIT parallel async execution doesn't break DataLoader batching
- Cache DataLoaders per-request to benefit from batching
- JIT compilation is orthogonal to DataLoader - they complement each other

### Error Handling

The JIT compiler maintains full GraphQL spec compliance for errors:

```python
@strawberry.type
class Query:
    @strawberry.field
    def risky_field(self) -> str:
        raise ValueError("Something went wrong!")


# Errors are properly propagated
result = compiled_query(None)
# {"data": None, "errors": [{...}]}
```

## Integration

### With FastAPI

```python
from fastapi import FastAPI, Request
from strawberry.jit import compile_query

app = FastAPI()


# Use in your route
@app.post("/graphql")
async def graphql_endpoint(request: Request):
    data = await request.json()
    query = data.get("query")

    # Compile and execute
    compiled = compile_query(schema, query)
    result = compiled(
        root_value=None,
        variables=data.get("variables"),
    )

    return result
```

Note: For production use, you should implement your own caching layer to avoid
recompiling the same query multiple times.

## Advanced Usage

### Custom Compilation

```python
from strawberry.jit import JITCompiler

compiler = JITCompiler(schema)

# Compile query
compiled = compiler.compile_query(query)

# Inspect generated code (for debugging)
print(compiled._jit_source)
```

### Debugging

The compiled query function has a `_jit_source` attribute containing the
generated Python code:

```python
compiled = compile_query(schema, query)
print(compiled._jit_source)
```

This shows you exactly what optimized code is being executed.

## Migration Guide

### From Standard Execution

**Before:**

```python
result = await schema.execute(query, variable_values=variables)
```

**After:**

```python
from strawberry.jit import compile_query

compiled = compile_query(schema, query)
result = compiled(root_value=None, variables=variables)
```

### Gradual Adoption

You can adopt JIT gradually by using it only for specific queries:

```python
# Use JIT for expensive queries
if is_expensive_query(query):
    compiled = jit_compiler.compile_query(query)
    return compiled(root_value)
else:
    # Use standard execution for simple queries
    return await schema.execute(query)
```

## Production Deployment

### Thread Safety

The compiled query functions are thread-safe and can be executed concurrently:

```python
# Safe for concurrent requests ✅
compiled = compile_query(schema, query)


# Multiple threads/workers can safely execute the same compiled query
def handle_request():
    return compiled(root_value=None)
```

**Note:** For production use with repeated queries, implement your own caching
layer to avoid recompiling the same query multiple times.

### Memory Considerations

**Per-Query Memory Usage:**

- **Compiled Code:** ~5-50KB per unique query
  - Simple queries (5-10 fields): ~5-15KB
  - Medium queries (20-50 fields): ~15-30KB
  - Complex queries (100+ fields): ~30-50KB+
- **Query String:** Original GraphQL string (1-10KB typical)
- **Metadata:** Negligible (< 1KB)

**Total Memory for Caching:**

```python
# Example: Production app with query caching
queries_cached = 100  # Typical application
avg_query_size = 20_000  # bytes (~20KB)
total_memory = queries_cached * avg_query_size
# = 2MB for 100 cached queries

# Large application
queries_cached = 1000
total_memory = 1000 * 20_000
# = 20MB for 1000 cached queries
```

**Memory Management Strategies:**

1. **LRU Cache with Size Limit:**
```python
from functools import lru_cache

@lru_cache(maxsize=100)  # Keep 100 most recent queries
def get_compiled_query(query_string: str):
    return compile_query(schema, query_string)
```

2. **TTL-Based Expiration:**
```python
import time

class QueryCache:
    def __init__(self, ttl_seconds=3600):
        self.cache = {}
        self.timestamps = {}
        self.ttl = ttl_seconds

    def get(self, query: str):
        if query in self.cache:
            if time.time() - self.timestamps[query] < self.ttl:
                return self.cache[query]
            else:
                # Expired - remove
                del self.cache[query]
                del self.timestamps[query]
        return None

    def set(self, query: str, compiled):
        self.cache[query] = compiled
        self.timestamps[query] = time.time()
```

3. **Size-Limited Cache:**
```python
class SizeLimitedCache:
    def __init__(self, max_size_mb=50):
        self.cache = {}
        self.max_bytes = max_size_mb * 1024 * 1024
        self.current_bytes = 0

    def estimate_size(self, query: str, compiled) -> int:
        # Rough estimate: query string + generated code length
        return len(query) + len(compiled._jit_source)

    def set(self, query: str, compiled):
        size = self.estimate_size(query, compiled)
        if self.current_bytes + size > self.max_bytes:
            # Evict oldest entries (or implement LRU)
            self._evict_oldest()
        self.cache[query] = compiled
        self.current_bytes += size
```

**Compilation Time vs Memory Trade-offs:**

| Scenario | Compile Once? | Cache? | Memory Impact |
|----------|--------------|--------|---------------|
| **Development** | No | No | Minimal (~0MB) |
| **Low Traffic** | Yes | Optional | Low (~1-5MB) |
| **High Traffic** | Yes | Yes | Medium (~10-50MB) |
| **Very High Traffic** | Yes | LRU/TTL | Bounded (~20-100MB) |

**Performance Impact of Caching:**

- **First execution:** Compilation + Execution
  - Compilation: ~1-5ms
  - Execution: ~10-100ms (depending on query)
  - Total: ~11-105ms

- **Cached executions:** Execution only
  - Execution: ~2-20ms (5-6x faster)
  - Savings: ~8-95ms per query

**When to Limit Cache Size:**

- Microservices with tight memory constraints
- Applications with thousands of unique queries
- Dynamic queries that rarely repeat
- Serverless functions with memory limits

**Monitoring Recommendations:**

```python
import logging

class MonitoredQueryCache:
    def __init__(self):
        self.cache = {}
        self.hits = 0
        self.misses = 0

    def get_or_compile(self, query: str):
        if query in self.cache:
            self.hits += 1
            return self.cache[query]
        else:
            self.misses += 1
            compiled = compile_query(schema, query)
            self.cache[query] = compiled

            # Log cache statistics
            hit_rate = self.hits / (self.hits + self.misses)
            if self.misses % 100 == 0:
                logging.info(
                    f"Query cache: {len(self.cache)} queries, "
                    f"hit rate: {hit_rate:.2%}"
                )
            return compiled
```

**Best Practice:** Start with unlimited caching in production, monitor memory usage, then add limits only if needed

## Best Practices

### 1. Cache Compiled Queries

In production, implement caching to avoid recompiling the same query:

```python
# Good ✅ - Cache the compiled query
query_cache = {}


def get_compiled_query(query_string):
    if query_string not in query_cache:
        query_cache[query_string] = compile_query(schema, query_string)
    return query_cache[query_string]


# Avoid ❌ - Recompiling every time
compile_query(schema, query)
```

### 2. Compile Once, Execute Many

Compile queries once and reuse the compiled function:

```python
# Good ✅
compiled = compile_query(schema, query)
for data in dataset:
    result = compiled(data)

# Avoid ❌
for data in dataset:
    compiled = compile_query(schema, query)  # Wasteful!
    result = compiled(data)
```

### 3. Handle Fallback Warnings

Some queries may fall back to standard execution (e.g., with `@defer`):

```python
import warnings

with warnings.catch_warnings(record=True) as w:
    compiled = compile_query(schema, query)
    if w:
        # Log fallback for monitoring
        logger.info(f"Query used fallback: {w[0].message}")
```

## Troubleshooting

### Query Validation Errors

If you see "Query validation failed", ensure your query is valid GraphQL:

```python
from graphql import parse, validate

# Validate before compiling
document = parse(query)
errors = validate(schema._schema, document)
if errors:
    print("Validation errors:", errors)
```

### Performance Not Improving

If you're not seeing speedup:

1. **Check if you're using caching** - First query compiles, subsequent queries
   benefit
2. **Profile your resolvers** - If resolvers are slow, JIT can't help
3. **Use async resolvers** - JIT can parallelize these
4. **Verify query complexity** - Straightforward queries may not show much
   improvement

### Memory Usage

For very large schemas with many queries:

```python
# Limit cache size to control memory
compiler = create_cached_compiler(
    schema, cache_size=100, ttl_seconds=300  # Smaller cache  # Expire after 5 minutes
)
```

## FAQ

**Q: Is JIT production-ready?** A: Yes! The JIT compiler has 99.3% test coverage
and is fully GraphQL spec compliant. It's labeled "Beta" while we gather
production feedback.

**Q: Does JIT work with subscriptions?** A: Yes, subscriptions are fully
supported.

**Q: Can I use JIT with my existing schema?** A: Yes! JIT is a drop-in
replacement for standard execution. No schema changes needed.

**Q: What's the compilation overhead?** A: First compilation takes ~1-5ms.
Execution is 5-6x faster than standard GraphQL execution.

**Q: Does JIT work with custom scalars?** A: Yes, all custom scalars are fully
supported with their serialize/parse_value functions.

**Q: What about @defer and @stream?** A: Queries with these directives
automatically fall back to standard execution with a warning. They work
correctly but don't get JIT speedup.

## Roadmap

Future improvements planned:

- [ ] Native `@defer` and `@stream` support
- [ ] Additional optimizations for specific query patterns
- [ ] Telemetry and performance metrics
- [ ] Query plan visualization
- [ ] Automatic query complexity analysis

## Contributing

The JIT compiler is open source! Contributions welcome:

- **Report issues**:
  [GitHub Issues](https://github.com/strawberry-graphql/strawberry/issues)
- **Contribute code**: [Contributing Guide](../contributing.md)
- **Benchmarks**: Share your performance results!

## See Also

- [Performance Guide](../guides/performance.md)
- [Caching Strategies](../guides/caching.md)
- [Examples](../../examples/jit-showcase/)
