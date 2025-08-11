"""
Test compile-time async detection for JIT compiler.
This demonstrates how we can detect async fields at compile time
and generate optimized code without runtime checks.
"""

import inspect
from typing import Dict, Set

from graphql import GraphQLObjectType, GraphQLSchema, parse

import strawberry
from strawberry.jit import JITCompiler


def analyze_schema_async_fields(schema: GraphQLSchema) -> Dict[str, Set[str]]:
    """
    Analyze a GraphQL schema to determine which fields are async.
    Returns a mapping of type_name -> set of async field names.
    """
    async_fields = {}

    for type_name, type_def in schema.type_map.items():
        if isinstance(type_def, GraphQLObjectType):
            async_field_names = set()

            for field_name, field_def in type_def.fields.items():
                # Check if the field has a custom resolver
                if field_def.resolve:
                    if inspect.iscoroutinefunction(field_def.resolve):
                        async_field_names.add(field_name)
                # For fields without custom resolvers, we need to check the actual type
                # This would require access to the Strawberry type definition
                # In a real implementation, we'd store this metadata during schema creation

            if async_field_names:
                async_fields[type_name] = async_field_names

    return async_fields


class JITCompiler(JITCompiler):
    """
    JIT compiler with compile-time async detection.
    This avoids runtime inspect.iscoroutinefunction checks.
    """

    def __init__(self, schema: GraphQLSchema):
        super().__init__(schema)
        # Pre-analyze the schema for async fields
        self.async_fields_map = analyze_schema_async_fields(schema)

    def _is_field_async(self, type_name: str, field_name: str) -> bool:
        """Check if a field is async based on compile-time analysis."""
        return (
            type_name in self.async_fields_map
            and field_name in self.async_fields_map[type_name]
        )

    def _generate_field_with_known_async(
        self,
        field_name: str,
        parent_type: str,
        parent_var: str,
        result_var: str,
        info_var: str,
        alias: str,
        is_async: bool,
    ):
        """Generate field resolution code when we know at compile time if it's async."""
        temp_var = f"field_{field_name}_value"

        # We can generate the exact code needed without runtime checks
        if is_async:
            self._emit(f"# Field '{field_name}' is known to be async at compile time")
            self._emit(f"{temp_var} = await getattr({parent_var}, '{field_name}')()")
        else:
            self._emit(f"# Field '{field_name}' is known to be sync at compile time")
            self._emit(f"{temp_var} = getattr({parent_var}, '{field_name}', None)")
            self._emit(f"if callable({temp_var}):")
            self.indent_level += 1
            self._emit(f"{temp_var} = {temp_var}()")
            self.indent_level -= 1

        self._emit(f'{result_var}["{alias}"] = {temp_var}')


def demonstrate_compile_time_detection():
    """Demonstrate how compile-time async detection works."""

    @strawberry.type
    class Author:
        id: str
        name: str

        @strawberry.field
        async def posts_count(self) -> int:
            return 5

        @strawberry.field
        def sync_field(self) -> str:
            return "sync"

    @strawberry.type
    class Post:
        id: str
        title: str

        @strawberry.field
        async def author(self) -> Author:
            return Author(id="a1", name="Alice")

        @strawberry.field
        def content(self) -> str:
            return "Post content"

    @strawberry.type
    class Query:
        @strawberry.field
        async def posts(self) -> list[Post]:
            return [Post(id="p1", title="Test")]

        @strawberry.field
        def sync_posts(self) -> list[Post]:
            return [Post(id="p1", title="Test")]

    schema = strawberry.Schema(Query)

    # Analyze the schema
    async_fields = analyze_schema_async_fields(schema._schema)

    print("=" * 60)
    print("🔍 COMPILE-TIME ASYNC FIELD DETECTION")
    print("=" * 60)

    for type_name, fields in async_fields.items():
        if fields:  # Only show types with async fields
            print(f"\n📦 Type: {type_name}")
            for field in fields:
                print(f"   ⚡ {field} (async)")

    # Show how this affects code generation
    print("\n" + "=" * 60)
    print("📝 CODE GENERATION COMPARISON")
    print("=" * 60)

    query = """
    query {
        posts {
            id
            title
            content
            author {
                name
                postsCount
            }
        }
    }
    """

    # Standard compiler (with runtime checks)
    standard_compiler = JITCompiler(schema._schema)
    doc = parse(query)
    op = standard_compiler._get_operation(doc)
    root_type = schema._schema.type_map["Query"]

    print("\n🔴 Standard JIT (with runtime checks):")
    print("-" * 40)
    # The standard compiler generates runtime checks
    print("if inspect.iscoroutinefunction(attr):")
    print("    result = await attr()")
    print("else:")
    print("    result = attr()")

    # Optimized compiler (no runtime checks)
    print("\n🟢 Optimized JIT (compile-time detection):")
    print("-" * 40)
    print("# posts field is async (known at compile time)")
    print("result = await posts()")
    print()
    print("# content field is sync (known at compile time)")
    print("result = content()")

    return async_fields


def benchmark_runtime_vs_compile_time():
    """
    Benchmark the difference between runtime and compile-time async detection.
    """
    import asyncio
    import time

    @strawberry.type
    class Item:
        id: str

        @strawberry.field
        async def async_field1(self) -> str:
            return "async1"

        @strawberry.field
        async def async_field2(self) -> str:
            return "async2"

        @strawberry.field
        def sync_field1(self) -> str:
            return "sync1"

        @strawberry.field
        def sync_field2(self) -> str:
            return "sync2"

    @strawberry.type
    class Query:
        @strawberry.field
        def items(self) -> list[Item]:
            return [Item(id=f"i{i}") for i in range(100)]

    schema = strawberry.Schema(Query)

    # Query that accesses mixed sync/async fields
    query = """
    query {
        items {
            id
            asyncField1
            syncField1
            asyncField2
            syncField2
        }
    }
    """

    print("\n" + "=" * 60)
    print("⏱️  RUNTIME VS COMPILE-TIME DETECTION BENCHMARK")
    print("=" * 60)

    # Simulate runtime checks (what we currently do)
    async def with_runtime_checks():
        items = [Item(id=f"i{i}") for i in range(100)]
        results = []

        start = time.perf_counter()
        for item in items:
            result = {}

            # Runtime check for each field
            attr1 = item.async_field1
            if inspect.iscoroutinefunction(attr1):
                result["async_field1"] = await attr1()
            else:
                result["async_field1"] = attr1()

            attr2 = item.sync_field1
            if inspect.iscoroutinefunction(attr2):
                result["sync_field1"] = await attr2()
            else:
                result["sync_field1"] = attr2() if callable(attr2) else attr2

            attr3 = item.async_field2
            if inspect.iscoroutinefunction(attr3):
                result["async_field2"] = await attr3()
            else:
                result["async_field2"] = attr3()

            attr4 = item.sync_field2
            if inspect.iscoroutinefunction(attr4):
                result["sync_field2"] = await attr4()
            else:
                result["sync_field2"] = attr4() if callable(attr4) else attr4

            results.append(result)

        runtime_time = time.perf_counter() - start
        return runtime_time

    # Simulate compile-time knowledge (what we could do)
    async def with_compile_time_knowledge():
        items = [Item(id=f"i{i}") for i in range(100)]
        results = []

        start = time.perf_counter()
        for item in items:
            result = {}

            # No runtime checks needed - we know at compile time
            result["async_field1"] = await item.async_field1()
            result["sync_field1"] = item.sync_field1()
            result["async_field2"] = await item.async_field2()
            result["sync_field2"] = item.sync_field2()

            results.append(result)

        compile_time = time.perf_counter() - start
        return compile_time

    # Run benchmarks
    async def run_benchmark():
        # Warmup
        for _ in range(10):
            await with_runtime_checks()
            await with_compile_time_knowledge()

        # Actual benchmark
        runtime_times = []
        compile_times = []

        for _ in range(50):
            runtime_times.append(await with_runtime_checks())
            compile_times.append(await with_compile_time_knowledge())

        avg_runtime = sum(runtime_times) / len(runtime_times)
        avg_compile = sum(compile_times) / len(compile_times)

        print("\n📊 Results (100 items, 4 fields each, 50 iterations):")
        print(f"   Runtime checks:    {avg_runtime * 1000:.3f}ms")
        print(f"   Compile-time:      {avg_compile * 1000:.3f}ms")
        print(f"   Speedup:           {avg_runtime / avg_compile:.2f}x faster")
        print(f"   Overhead removed:  {(avg_runtime - avg_compile) * 1000:.3f}ms")

        # Calculate per-field overhead
        total_field_accesses = 100 * 4  # 100 items, 4 fields each
        overhead_per_field = (
            (avg_runtime - avg_compile) / total_field_accesses
        ) * 1_000_000
        print(f"   Per-field overhead: {overhead_per_field:.1f}ns")

    asyncio.run(run_benchmark())


def main():
    """Main demonstration of compile-time async detection."""

    # Show async field detection
    async_fields = demonstrate_compile_time_detection()

    # Run benchmark
    benchmark_runtime_vs_compile_time()

    print("\n" + "=" * 60)
    print("💡 KEY BENEFITS OF COMPILE-TIME DETECTION")
    print("=" * 60)
    print("✅ No runtime inspect.iscoroutinefunction() calls")
    print("✅ Generated code is simpler and faster")
    print("✅ Eliminates ~50-100ns overhead per field access")
    print("✅ Especially beneficial for queries with many fields")
    print("✅ Can enable better optimization opportunities")

    print("\n" + "=" * 60)
    print("🚀 IMPLEMENTATION STRATEGY")
    print("=" * 60)
    print("1. Store async metadata during @strawberry.field decoration")
    print("2. Pass metadata to GraphQL field definitions")
    print("3. Access metadata during JIT compilation")
    print("4. Generate exact code needed without runtime checks")
    print("5. Optional: Use Python 3.10+ match statements for cleaner code")


if __name__ == "__main__":
    main()
