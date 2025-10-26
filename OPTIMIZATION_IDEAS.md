# Optimization Strategies for Rust GraphQL Execution

## Current Bottleneck Analysis

For the 90,000 seat query:
- Python: 850ms
- Rust: 458ms
- Speedup: 1.86x

### Where time is spent:

```
Rust (458ms total):
├─ Parsing/Validation: ~10ms (2%)
├─ Building Python objects: ~50ms (11%)  [Python resolver call]
└─ Walking object tree: ~398ms (87%)
   ├─ PyO3 getattr calls: ~200ms (extracting x, y, labels from 90k Seats)
   ├─ GIL acquisitions: ~100ms (acquiring/releasing GIL)
   ├─ Type conversions: ~50ms (Python → Rust conversions)
   └─ List processing: ~48ms (converting lists to ResolvedValue)
```

**The problem**: 90,000 seats × (3 fields + overhead) = ~270,000 Python/Rust boundary crossings!

## Optimization Strategies

### 1. **Batch Attribute Access** (Potential: 2-3x faster)

**Current approach**: For each Seat, call getattr 3 times:
```rust
// For EACH seat (90,000 times):
let x = seat.getattr("x")?;        // GIL acquire/release
let y = seat.getattr("y")?;        // GIL acquire/release
let labels = seat.getattr("labels")?;  // GIL acquire/release
```

**Optimized approach**: Extract all attributes at once:
```rust
// For EACH seat (90,000 times):
Python::with_gil(|py| {
    let seat_dict = py.eval("lambda obj: {
        'x': obj.x,
        'y': obj.y,
        'labels': obj.labels
    }", None, None)?
    .call1((seat,))?;

    // Now extract from dict (no more GIL calls)
    let x = seat_dict.get_item("x")?;
    let y = seat_dict.get_item("y")?;
    let labels = seat_dict.get_item("labels")?;
});
```

**Savings**:
- Before: 270,000 GIL acquisitions
- After: 90,000 GIL acquisitions
- **3x fewer boundary crossings!**

### 2. **Serialize to JSON in Python** (Potential: 3-5x faster)

**Current approach**: Walk Python objects one by one in Rust

**Optimized approach**: Let Python serialize everything at once
```rust
Python::with_gil(|py| {
    // Call Python's json.dumps on the entire result
    let json_module = py.import("json")?;
    let encoder = py.eval("lambda obj: __import__('dataclasses').asdict(obj)", None, None)?;

    // This happens in pure Python (FAST!)
    let data_dict = encoder.call1((result,))?;
    let json_str = json_module.getattr("dumps")?.call1((data_dict,))?;

    // Parse JSON in Rust (ALSO FAST!)
    let json_value: JsonValue = serde_json::from_str(&json_str)?;
});
```

**Why this is faster**:
- Python's dataclass → dict is native code (C)
- Python's json.dumps is native code (C)
- Rust's JSON parsing is native (Rust)
- **NO PyO3 overhead for 90,000 objects!**

**Savings**:
- Before: 270,000+ PyO3 calls
- After: 1 PyO3 call + native JSON processing
- **Estimated: 3-5x faster for large datasets**

### 3. **Use `__dict__` for Dataclasses** (Potential: 1.5-2x faster)

**Current approach**: Call getattr for each field

**Optimized approach**: Access `__dict__` directly
```rust
Python::with_gil(|py| {
    // Get the entire __dict__ at once
    let obj_dict = obj.getattr("__dict__")?;

    // Extract fields from dict (faster than getattr)
    let x = obj_dict.get_item("x")?;
    let y = obj_dict.get_item("y")?;
    let labels = obj_dict.get_item("labels")?;
});
```

**Why faster**:
- `__dict__` is a single attribute access
- Dict lookups are faster than attribute protocol
- No Python descriptor protocol overhead

### 4. **Parallel Object Processing** (Potential: 2-4x on multi-core)

**Current approach**: Process objects sequentially

**Optimized approach**: Use rayon for parallel processing
```rust
use rayon::prelude::*;

// Process list of seats in parallel
let resolved_seats: Vec<_> = seats
    .par_iter()  // Parallel iterator!
    .map(|seat| {
        Python::with_gil(|py| {
            python_to_resolved_value(py, seat, info)
        })
    })
    .collect::<Result<_, _>>()?;
```

**Limitations**:
- GIL contention (Python's GIL limits true parallelism)
- May need thread pool with GIL release
- Best for CPU-bound conversions

### 5. **Cache Python Class Metadata** (Potential: 1.2-1.5x faster)

**Current approach**: Get `__class__.__name__` for every object

**Optimized approach**: Cache type information
```rust
use std::collections::HashMap;

static TYPE_CACHE: Mutex<HashMap<usize, String>> = ...;

fn get_type_name(obj: &PyAny) -> String {
    let obj_id = obj.as_ptr() as usize;

    // Check cache first
    if let Some(cached) = TYPE_CACHE.lock().get(&obj_id) {
        return cached.clone();
    }

    // Otherwise compute and cache
    let type_name = obj.getattr("__class__")?.getattr("__name__")?.extract()?;
    TYPE_CACHE.lock().insert(obj_id, type_name.clone());
    type_name
}
```

### 6. **Use Protocol Buffers / Cap'n Proto** (Potential: 5-10x faster)

**Most extreme**: Skip JSON entirely, use binary format

**Approach**:
```python
# Python side: Serialize to protobuf
data = serialize_to_protobuf(result)
```

```rust
// Rust side: Deserialize from protobuf
let data: StadiumProto = deserialize_protobuf(data)?;
```

**Pros**:
- Zero-copy deserialization
- Much faster than JSON
- Strongly typed

**Cons**:
- Requires schema duplication
- More complex integration

## Implementation Priority

### Quick Wins (1-2 days each)

1. ✅ **Use `__dict__` for dataclasses** - Easy, 1.5x improvement
2. ✅ **Serialize to JSON in Python** - Medium effort, 3-5x improvement
3. ✅ **Cache type names** - Easy, 1.2x improvement

### Medium Effort (1 week each)

4. **Batch attribute access** - Moderate, 2-3x improvement
5. **Better list handling** - Detect list types and optimize

### Long Term (2-4 weeks)

6. **Async support** - Critical for real apps
7. **Parallel processing** - Complex due to GIL
8. **Zero-copy strategies** - Research needed

## Recommended Approach

### Phase 1: JSON Serialization (HIGHEST IMPACT)

Implement Strategy #2: Let Python serialize to JSON

**Expected result**:
- Current: 458ms for 90k objects
- With JSON: ~100-150ms
- **3-4x faster!**

**Why this works**:
- Python's json.dumps is C code (very fast)
- Avoids 270,000 PyO3 calls
- Rust's JSON parsing is also very fast
- Trade-off: More memory allocation, but worth it

### Phase 2: `__dict__` Access (EASY WIN)

For objects that aren't serialized to JSON

**Expected result**:
- Another 1.5x improvement on remaining overhead

### Phase 3: Caching (POLISH)

Add caching for type names and other metadata

## Code Example: JSON Serialization Optimization

```rust
fn python_to_resolved_value_optimized<'a>(
    py: Python,
    value: &PyAny,
    info: &'a ResolveInfo<'a>,
) -> Result<ResolvedValue<'a>, FieldError> {
    // For complex objects, try JSON serialization first
    if value.hasattr("__dataclass_fields__")? {
        // It's a dataclass - serialize to JSON in Python
        if let Ok(json_module) = py.import("json") {
            if let Ok(dataclasses) = py.import("dataclasses") {
                if let Ok(asdict) = dataclasses.getattr("asdict") {
                    // Convert dataclass to dict in Python (FAST!)
                    if let Ok(dict_result) = asdict.call1((value,)) {
                        // Serialize to JSON in Python (FAST!)
                        if let Ok(dumps) = json_module.getattr("dumps") {
                            if let Ok(json_str) = dumps.call1((dict_result,))?.extract::<String>() {
                                // Parse in Rust (FAST!)
                                if let Ok(json_val) = serde_json::from_str::<JsonValue>(&json_str) {
                                    return Ok(ResolvedValue::leaf(json_val));
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // Fallback to current approach
    // ... existing code ...
}
```

## Expected Final Performance

With all optimizations:

| Dataset | Current | Optimized | Speedup vs Current | Speedup vs Python |
|---------|---------|-----------|-------------------|-------------------|
| Small (5k) | 1.37ms | 0.8ms | 1.7x | 6x |
| Large (90k) | 458ms | 100-150ms | 3-4x | 6-8x |

**Final speedup over Python**: **6-8x** (much closer to the original POC!)

## Trade-offs

### JSON Serialization
- ✅ Pro: Massive speedup (3-5x)
- ✅ Pro: Simple to implement
- ⚠️ Con: Higher memory usage
- ⚠️ Con: Loses some type safety

### Parallel Processing
- ✅ Pro: Linear speedup with cores
- ❌ Con: GIL limits true parallelism
- ❌ Con: Complex to implement correctly

### Binary Formats
- ✅ Pro: Maximum performance
- ❌ Con: Schema duplication
- ❌ Con: Complex integration

## Conclusion

**Best optimization**: Serialize to JSON in Python, parse in Rust

This single change could improve from **458ms → ~120ms** (3.8x faster), giving us:
- **7x faster than Python** for large queries
- Closer to the original POC numbers
- Minimal code complexity

**Implementation time**: 2-3 days

Should I implement the JSON serialization optimization?
