"""
Test performance improvements from using the native Strawberry type map.
"""

import time
from typing import List, Optional

import strawberry
from strawberry.jit import JITCompiler
from strawberry.schema.config import StrawberryConfig


@strawberry.type
class Author:
    id: str
    full_name: str  # -> fullName in GraphQL
    email_address: str  # -> emailAddress in GraphQL
    total_posts_count: int  # -> totalPostsCount in GraphQL

    @strawberry.field
    def recent_posts_by_category(self, category_name: str) -> List[str]:
        """Field with snake_case name and argument."""
        return []


@strawberry.type
class Post:
    id: str
    title: str
    author_name: str  # -> authorName in GraphQL
    is_published: bool  # -> isPublished in GraphQL
    view_count: int  # -> viewCount in GraphQL
    created_at_timestamp: float  # -> createdAtTimestamp in GraphQL
    last_modified_by_user: Optional[str]  # -> lastModifiedByUser in GraphQL


@strawberry.type
class Query:
    @strawberry.field
    def get_posts_by_author(
        self,
        author_id: str,
        include_drafts: bool = False,
        max_results: int = 10,
    ) -> List[Post]:
        """Get posts with multiple snake_case arguments."""
        return []

    @strawberry.field
    def find_author_by_email(self, email_address: str) -> Optional[Author]:
        """Find author by email."""
        return None

    @strawberry.field
    def search_posts_with_filters(
        self,
        search_query: str,
        author_ids: Optional[List[str]] = None,
        is_published: Optional[bool] = None,
        min_view_count: Optional[int] = None,
        max_view_count: Optional[int] = None,
    ) -> List[Post]:
        """Complex search with many snake_case parameters."""
        return []


def benchmark_name_conversion():
    """Benchmark the performance of name conversions."""
    schema = strawberry.Schema(Query)
    config = StrawberryConfig()

    # Fields that need conversion
    field_names = [
        "getPostsByAuthor",
        "findAuthorByEmail",
        "searchPostsWithFilters",
        "authorName",
        "isPublished",
        "viewCount",
        "createdAtTimestamp",
        "lastModifiedByUser",
        "recentPostsByCategory",
        "totalPostsCount",
        "emailAddress",
        "fullName",
    ]

    iterations = 100000

    # Benchmark old way: repeated name conversion
    # Simulate converting from camelCase to snake_case manually
    import re

    def camel_to_snake(name):
        # Simple camelCase to snake_case conversion
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    start = time.perf_counter()
    for _ in range(iterations):
        for graphql_name in field_names:
            # Simulate what would happen without pre-computed names
            python_name = camel_to_snake(graphql_name)
    old_time = time.perf_counter() - start

    # Benchmark new way: using type map with pre-computed names
    type_map = schema.type_map

    # Pre-fetch the field maps for the types we'll be accessing
    query_fields = type_map.field_maps.get("Query", None)
    post_fields = type_map.field_maps.get("Post", None)
    author_fields = type_map.field_maps.get("Author", None)

    start = time.perf_counter()
    for _ in range(iterations):
        # Simulate field lookups using pre-computed names
        if query_fields:
            query_fields.get_python_name("getPostsByAuthor")
            query_fields.get_python_name("findAuthorByEmail")
            query_fields.get_python_name("searchPostsWithFilters")
        if post_fields:
            post_fields.get_python_name("authorName")
            post_fields.get_python_name("isPublished")
            post_fields.get_python_name("viewCount")
            post_fields.get_python_name("createdAtTimestamp")
            post_fields.get_python_name("lastModifiedByUser")
        if author_fields:
            author_fields.get_python_name("recentPostsByCategory")
            author_fields.get_python_name("totalPostsCount")
            author_fields.get_python_name("emailAddress")
            author_fields.get_python_name("fullName")
    new_time = time.perf_counter() - start

    speedup = old_time / new_time
    per_lookup_saving_ns = (
        (old_time - new_time) / (iterations * len(field_names))
    ) * 1_000_000_000

    print("\\n📊 Name Conversion Performance:")
    print(f"   Old way (repeated conversion): {old_time * 1000:.2f}ms")
    print(f"   New way (pre-computed lookup): {new_time * 1000:.2f}ms")
    print(f"   Speedup: {speedup:.1f}x faster")
    print(f"   Per-lookup saving: {per_lookup_saving_ns:.1f}ns")

    assert speedup > 5.0, f"Expected significant speedup, got {speedup:.1f}x"


def benchmark_field_access():
    """Benchmark field access performance."""
    schema = strawberry.Schema(Query)

    iterations = 100000

    # Benchmark old way: going through GraphQL Core
    graphql_schema = schema._schema
    start = time.perf_counter()
    for _ in range(iterations):
        # Simulate what JIT compiler would do without type map
        query_type = graphql_schema.type_map["Query"]
        field = query_type.fields.get("getPostsByAuthor")
        if field and hasattr(field, "extensions"):
            strawberry_field = field.extensions.get("strawberry-definition")
    old_time = time.perf_counter() - start

    # Benchmark new way: direct type map access
    type_map = schema.type_map
    start = time.perf_counter()
    for _ in range(iterations):
        # Direct access through type map
        field = type_map.get_field("Query", "getPostsByAuthor")
    new_time = time.perf_counter() - start

    speedup = old_time / new_time
    per_access_saving_ns = ((old_time - new_time) / iterations) * 1_000_000_000

    print("\\n📊 Field Access Performance:")
    print(f"   GraphQL Core access: {old_time * 1000:.2f}ms")
    print(f"   Type map access: {new_time * 1000:.2f}ms")
    print(f"   Speedup: {speedup:.1f}x faster")
    print(f"   Per-access saving: {per_access_saving_ns:.1f}ns")

    # Even a small speedup is good, the main benefit is cleaner code
    # and the massive speedup in name conversion
    assert speedup >= 1.0, f"Should be at least as fast, got {speedup:.1f}x"


def test_jit_with_type_map():
    """Test that JIT compiler works with Strawberry schema and type map."""
    schema = strawberry.Schema(Query)

    # Create JIT compiler with Strawberry schema (not GraphQL Core schema)
    compiler = JITCompiler(schema)

    # Verify it has access to the type map
    assert compiler.type_map is not None
    assert compiler.strawberry_schema is schema

    # Compile a query that uses snake_case fields
    query = """
    query {
        getPostsByAuthor(authorId: "a1", includeDrafts: true) {
            id
            title
            authorName
            isPublished
            viewCount
        }
    }
    """

    compiled_fn = compiler.compile_query(query)

    # Execute the query
    result = compiled_fn(Query())

    # Should execute without errors
    assert "getPostsByAuthor" in result
    assert result["getPostsByAuthor"] == []

    print("✅ JIT compiler works with Strawberry schema and type map!")


def benchmark_jit_compilation_with_type_map():
    """Benchmark JIT compilation speed with type map."""
    schema = strawberry.Schema(Query)

    query = """
    query ComplexQuery {
        posts1: getPostsByAuthor(authorId: "a1") {
            id
            title
            authorName
            isPublished
            viewCount
            createdAtTimestamp
            lastModifiedByUser
        }
        posts2: searchPostsWithFilters(
            searchQuery: "test",
            isPublished: true,
            minViewCount: 100
        ) {
            id
            title
            authorName
            viewCount
        }
        author: findAuthorByEmail(emailAddress: "test@example.com") {
            id
            fullName
            emailAddress
            totalPostsCount
            recentPostsByCategory(categoryName: "tech")
        }
    }
    """

    iterations = 100

    # Since we only support Strawberry schemas now, we'll just benchmark
    # the compilation performance
    compiler = JITCompiler(schema)
    start = time.perf_counter()
    for _ in range(iterations):
        compiler.compile_query(query)
    compilation_time = time.perf_counter() - start

    print("\\n📊 JIT Compilation Performance:")
    print(
        f"   With Strawberry type map: {compilation_time * 1000:.2f}ms for {iterations} compilations"
    )
    print(f"   Average per compilation: {compilation_time * 1000 / iterations:.2f}ms")


if __name__ == "__main__":
    benchmark_name_conversion()
    benchmark_field_access()
    test_jit_with_type_map()
    benchmark_jit_compilation_with_type_map()
    print("\\n🎉 All performance tests passed!")
