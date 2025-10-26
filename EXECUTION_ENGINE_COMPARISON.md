# GraphQL Execution Engine Comparison for Strawberry

## Context

We want to accelerate GraphQL execution by using Rust, but:
- **Schema definition stays in Python** (Strawberry decorators)
- **Resolvers stay in Python** (user code)
- **Only execution logic moves to Rust**

This means we need a **pure execution engine**, not a full GraphQL server framework.

## Requirements

1. ✅ Fast execution of GraphQL queries
2. ✅ Can work with externally-defined schemas (not Rust-native)
3. ✅ Can call Python resolver functions
4. ✅ Minimal overhead for schema/type system setup
5. ✅ Production-ready and well-tested

## Options Analysis

### 1. **async-graphql** ❌ NOT SUITABLE

**What it is**: Full-featured GraphQL server framework

**Pros**:
- Modern async-first design
- Fastest among Rust GraphQL servers (~15% faster than Juniper)
- 4.44ms latency, 45k req/s (benchmark data)
- Very active development

**Cons**:
- ❌ **Tightly couples schema definition with execution**
- ❌ Designed for Rust-native schemas using derive macros
- ❌ Heavy web server focus (Actix/Tokio integration)
- ❌ Would need to translate entire Strawberry schema to Rust types
- ❌ Execution "was actually kinda slow" when used without its schema system

**Verdict**: Overkill. Built for people defining schemas in Rust, not for external schema execution.

### 2. **Juniper** ⚠️ MAYBE

**What it is**: GraphQL server library with flexible schema definition

**Pros**:
- Mature and stable
- Both sync and async execution
- 5.16ms latency, 39k req/s (benchmark data)
- More flexible schema definition than async-graphql
- Can separate schema from execution

**Cons**:
- ⚠️ Still designed as a server framework
- ⚠️ Schema definition still Rust-centric (macros)
- ⚠️ ~15% slower than async-graphql in benchmarks
- ⚠️ Would need significant work to use as execution-only library

**Verdict**: Possible but not ideal. Better separation than async-graphql, but still server-focused.

### 3. **apollo-compiler** ✅ INTERESTING!

**What it is**: GraphQL tooling library with execution support

**Pros**:
- ✅ **Designed for tooling, not servers**
- ✅ Has resolver-style execution built-in
- ✅ Trait-based, very flexible
- ✅ Can work with external schemas (SDL strings)
- ✅ Both sync (`ObjectValue`) and async (`AsyncObjectValue`) traits
- ✅ Lean - no web server baggage
- ✅ Part of Apollo (well-maintained)

**Cons**:
- ⚠️ Execution feature is newer (less battle-tested)
- ⚠️ Documentation is sparse
- ⚠️ No benchmark data vs other engines
- ⚠️ Maintainer says "kinda lightly maintained"

**How it works**:
```rust
use apollo_compiler::{Schema, ExecutableDocument};
use apollo_compiler::execution::{Execution, Response};
use apollo_compiler::resolvers::{ObjectValue, ResolverContext};

// Parse schema from SDL (can come from Python!)
let schema = Schema::parse("type Query { hello: String }", "schema.graphql")?;

// Parse query
let document = ExecutableDocument::parse(&schema, "{ hello }", "query.graphql")?;

// Create execution
let execution = Execution::new(&schema, &document)?;

// Implement resolver trait
struct Query;
impl ObjectValue for Query {
    fn resolve_field(&self, ctx: &ResolverContext) -> Option<Value> {
        match ctx.field_name() {
            "hello" => Some(Value::String("world".into())),
            _ => None
        }
    }
}

// Execute!
let response = execution.execute_sync(&Query)?;
```

**Verdict**: Most promising! Designed exactly for our use case.

### 4. **graphql-core (Python)** 📊 BASELINE

Current performance: **436ms for 45K objects**

- Pure Python implementation
- Full GraphQL spec compliance
- Already integrated with Strawberry

**Verdict**: This is what we're trying to beat!

## Performance Comparison

| Engine | Latency | Throughput | Notes |
|--------|---------|------------|-------|
| async-graphql | 4.44ms | 45k req/s | With Rust schema & resolvers |
| Juniper | 5.16ms | 39k req/s | With Rust schema & resolvers |
| apollo-compiler | ??? | ??? | No benchmarks available |
| graphql-core (Python) | **436ms** | ~2.3 req/s | Our baseline (45K objects) |

**Important**: The Rust benchmarks are for full server stacks with Rust resolvers. With Python resolvers, we'll have:
- Python call overhead
- GIL contention
- Slower than pure Rust, but still much faster than pure Python

**Realistic estimate with Python resolvers**: **10-20x faster** than graphql-core

## Recommendation

### ✅ **Use apollo-compiler** for POC

**Why**:
1. **Architecturally perfect**: Designed for external schemas, not Rust-native
2. **Minimal coupling**: Trait-based, easy to integrate
3. **Flexible**: Can parse schema from SDL (from Strawberry)
4. **Lean**: No web server dependencies
5. **Well-maintained**: Part of Apollo ecosystem

**POC Plan**:

```python
# Python side (Strawberry stays unchanged)
schema = strawberry.Schema(query=Query)
sdl = str(schema)  # Get SDL representation

# Rust side (new execution engine)
import strawberry_core_rs

result = strawberry_core_rs.execute(
    schema_sdl=sdl,
    query="{ stadium { name } }",
    root_value=root,
    resolvers=python_resolver_map,  # Python callbacks
)
```

**Rust implementation**:
```rust
use pyo3::prelude::*;
use apollo_compiler::{Schema, ExecutableDocument};
use apollo_compiler::execution::Execution;

#[pyfunction]
fn execute(
    schema_sdl: &str,
    query: &str,
    root_value: PyObject,
    resolvers: PyObject,
) -> PyResult<String> {
    // Parse schema from SDL
    let schema = Schema::parse(schema_sdl, "schema.graphql")?;

    // Parse query
    let document = ExecutableDocument::parse(&schema, query, "query.graphql")?;

    // Create execution
    let execution = Execution::new(&schema, &document)?;

    // Bridge to Python resolvers
    let resolver_bridge = PythonResolverBridge::new(root_value, resolvers);

    // Execute
    let response = execution.execute_sync(&resolver_bridge)?;

    Ok(serde_json::to_string(&response)?)
}
```

### Alternative: Juniper

If apollo-compiler doesn't work out:
- Juniper has better docs and more examples
- Proven in production
- Would need more work to decouple schema from execution

### Don't Use: async-graphql

Wrong tool for the job. Great if you're building a full Rust GraphQL server, but not for execution-only.

## Next Steps for POC

1. ✅ **Minimal apollo-compiler test** (1 day)
   - Parse schema from SDL
   - Execute simple query
   - Call Python resolver
   - Measure overhead

2. **If apollo-compiler works** (1 week)
   - Implement full resolver bridge
   - Handle all GraphQL types
   - Async resolver support
   - Error handling

3. **If apollo-compiler doesn't work** (1 week)
   - Try Juniper approach
   - Decouple schema from execution
   - Same resolver bridge

4. **Benchmark** (1 day)
   - Test with stadium benchmark
   - Compare vs graphql-core baseline
   - Measure Python call overhead

## Expected Results

### Best Case (apollo-compiler)
- **15-20x faster than graphql-core**
- Clean architecture (SDL-based)
- Easy to maintain

### Realistic Case (Juniper)
- **10-15x faster than graphql-core**
- More coupling with Rust type system
- More maintenance overhead

### Worst Case
- **5-10x faster than graphql-core**
- Still worth it, but maybe not worth the complexity
- Would need to optimize resolver bridge

## Key Insight

The bottleneck won't be the execution engine itself (all Rust options are fast). The bottleneck will be:

1. **Python resolver calls** (crossing the Python/Rust boundary)
2. **GIL contention** (if resolvers do I/O)
3. **Type conversion** (GraphQL values ↔ Python objects)

**Optimization focus**: Minimize boundary crossings and optimize the resolver bridge!

## Conclusion

**Go with apollo-compiler for the POC**. It's architecturally the best fit:
- Accepts SDL schemas (no Rust types needed)
- Trait-based resolvers (flexible)
- Lean and focused
- Part of Apollo (good long-term bet)

If it doesn't work out, Juniper is a solid fallback. But avoid async-graphql - it's built for a different use case.
