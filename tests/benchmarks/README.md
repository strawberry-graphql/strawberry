# Strawberry Benchmarks

This directory contains performance benchmarks for Strawberry GraphQL using [pytest-codspeed](https://github.com/CodSpeedHQ/pytest-codspeed).

## Running Benchmarks

### Running all benchmarks

```bash
pytest tests/benchmarks/ --codspeed
```

### Running a specific benchmark

```bash
pytest tests/benchmarks/test_stadium.py --codspeed
```

### Running with specific parameters

```bash
pytest tests/benchmarks/test_stadium.py::test_stadium[seats_per_row_500] --codspeed
```

## Benchmark Tests

### test_stadium.py

Benchmarks a complex nested query with a large dataset. This test creates a stadium with multiple stands, each containing thousands of seats. It's useful for testing Strawberry's performance with:

- Deeply nested object structures
- Large result sets (45,000 - 90,000+ objects)
- Multiple list fields at different levels
- Complex object resolution

**Parameters:**
- `seats_per_row=250`: ~45,000 total seats across 4 stands
- `seats_per_row=500`: ~90,000 total seats across 4 stands

### test_execute.py

Benchmarks basic query execution with patrons and pets.

### test_execute_with_extensions.py

Benchmarks query execution with various extensions enabled.

### test_subscriptions.py

Benchmarks subscription performance.

## Generating Flame Graphs

Flame graphs are a powerful visualization tool for profiling and understanding where your code spends time. They help identify performance bottlenecks in the execution path.

### Using py-spy

[py-spy](https://github.com/benfred/py-spy) is a sampling profiler for Python that can generate flame graphs.

#### Installation

```bash
pip install py-spy
```

#### Generate a flame graph

```bash
# Profile a specific benchmark test
py-spy record -o profile.svg --format speedscope -- pytest tests/benchmarks/test_stadium.py::test_stadium[seats_per_row_500] -v

# Or use the flame graph format directly
py-spy record -o flamegraph.svg -- pytest tests/benchmarks/test_stadium.py::test_stadium[seats_per_row_500] -v
```

#### View the flame graph

The generated SVG file can be opened in any web browser. Each box represents a function call, and the width represents the proportion of time spent in that function.

For speedscope format, upload the file to [speedscope.app](https://www.speedscope.app/).

### Using Austin

[Austin](https://github.com/P403n1x87/austin) is another statistical profiler for Python.

#### Installation

```bash
pip install austin-python
```

#### Generate a flame graph

```bash
# Profile and generate flame graph
austin -o profile.austin pytest tests/benchmarks/test_stadium.py::test_stadium[seats_per_row_500] -v

# Convert to flame graph format (requires flamegraph.pl from https://github.com/brendangregg/FlameGraph)
austin2speedscope profile.austin profile.speedscope.json
```

### Using Python's built-in cProfile with flameprof

For a simpler approach using Python's built-in profiler:

#### Installation

```bash
pip install flameprof
```

#### Generate a flame graph

```bash
# Profile with cProfile
python -m cProfile -o profile.stats -m pytest tests/benchmarks/test_stadium.py::test_stadium[seats_per_row_500] -v

# Generate flame graph
flameprof profile.stats > flamegraph.svg
```

### Interpreting Flame Graphs

- **Width**: The wider the box, the more time was spent in that function
- **Height**: The stack depth - how many functions were called to get there
- **Color**: Usually random, just for visual distinction (unless using differential flame graphs)
- **Top plateau boxes**: These are the functions where the program is actually spending time
- **Look for**: Wide boxes at the top of the stack - these are your hot paths

## CI/CD Integration

These benchmarks are integrated with CodSpeed in CI to track performance over time. Performance results are available in the CodSpeed dashboard for pull requests and commits.

## Best Practices

1. **Consistent Environment**: Run benchmarks on a quiet system with minimal background processes
2. **Multiple Runs**: The benchmark tool automatically runs tests multiple times to ensure statistical significance
3. **Warm-up**: The first run may be slower due to Python's JIT compilation and caching
4. **Isolation**: Use `pytest -k test_name` to run specific benchmarks in isolation for profiling

## Adding New Benchmarks

1. Create a new test file in `tests/benchmarks/`
2. Use the `@pytest.mark.benchmark` decorator
3. Accept `BenchmarkFixture` as a parameter
4. Create a `run()` function that executes your query
5. Call `benchmark(run)` to measure performance
6. Add assertions to verify the query executed correctly

Example:

```python
import asyncio
import pytest
from pytest_codspeed.plugin import BenchmarkFixture
import strawberry

@pytest.mark.benchmark
def test_my_benchmark(benchmark: BenchmarkFixture):
    # Define your schema
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self) -> str:
            return "world"

    schema = strawberry.Schema(query=Query)
    query = "{ hello }"

    def run():
        return asyncio.run(schema.execute(query))

    results = benchmark(run)
    assert results.errors is None
```

For complex queries, consider storing the GraphQL query in `tests/benchmarks/queries/` as a `.graphql` file.
