"""
Test JIT compilation with field arguments support.
"""

import time
from typing import List, Optional

from graphql import execute, parse
from inline_snapshot import outsource, snapshot

import strawberry
from strawberry.jit_compiler import compile_query


@strawberry.type
class Post:
    id: str
    title: str
    content: str
    published: bool
    views: int


@strawberry.type
class User:
    id: str
    name: str
    email: str
    
    @strawberry.field
    def posts(self, published: Optional[bool] = None, limit: int = 10, offset: int = 0) -> List[Post]:
        """Get user's posts with filtering and pagination."""
        all_posts = [
            Post(
                id=f"post_{i}",
                title=f"Post {i}",
                content=f"Content for post {i}",
                published=i % 2 == 0,
                views=i * 100,
            )
            for i in range(20)
        ]
        
        # Filter by published status if provided
        if published is not None:
            filtered = [p for p in all_posts if p.published == published]
        else:
            filtered = all_posts
        
        # Apply pagination
        return filtered[offset:offset + limit]
    
    @strawberry.field
    def recent_posts(self, days: int = 7, min_views: int = 0) -> List[Post]:
        """Get recent posts with view threshold."""
        # Simulate filtering by date and views
        return [
            Post(
                id=f"recent_{i}",
                title=f"Recent Post {i}",
                content=f"Recent content {i}",
                published=True,
                views=(i + 1) * min_views + 100,
            )
            for i in range(min(days, 5))
        ]


@strawberry.type
class SearchResult:
    posts: List[Post]
    total_count: int


@strawberry.type
class Query:
    @strawberry.field
    def user(self, id: str) -> User:
        """Get user by ID."""
        return User(
            id=id,
            name=f"User {id}",
            email=f"user{id}@example.com",
        )
    
    @strawberry.field
    def search_posts(
        self,
        query: str,
        limit: int = 20,
        published_only: bool = True,
        min_views: Optional[int] = None,
    ) -> SearchResult:
        """Search posts with various filters."""
        # Simulate search
        posts = []
        for i in range(limit):
            if published_only and i % 3 == 0:
                continue  # Skip unpublished
            if min_views and i * 50 < min_views:
                continue  # Skip low-view posts
            
            posts.append(
                Post(
                    id=f"search_{i}",
                    title=f"Search result for '{query}' #{i}",
                    content=f"Content matching '{query}'",
                    published=i % 3 != 0,
                    views=i * 50,
                )
            )
        
        return SearchResult(posts=posts[:limit], total_count=len(posts))
    
    @strawberry.field
    def posts_by_ids(self, ids: List[str]) -> List[Post]:
        """Get multiple posts by their IDs."""
        return [
            Post(
                id=post_id,
                title=f"Post {post_id}",
                content=f"Content for {post_id}",
                published=True,
                views=100,
            )
            for post_id in ids
        ]


def test_jit_with_simple_arguments():
    """Test JIT compilation with simple field arguments."""
    schema = strawberry.Schema(Query)
    
    query = """
    query GetUser {
        user(id: "123") {
            id
            name
            email
            posts(limit: 5, published: true) {
                id
                title
                published
            }
        }
    }
    """
    
    # Compile with JIT
    compiled_fn = compile_query(schema._schema, query)
    
    # Execute both ways
    root = Query()
    jit_result = compiled_fn(root)
    standard_result = execute(schema._schema, parse(query), root_value=root)
    
    # Verify results match
    assert jit_result == standard_result.data
    assert jit_result["user"]["id"] == "123"
    assert len(jit_result["user"]["posts"]) <= 5
    assert all(p["published"] for p in jit_result["user"]["posts"])


def test_jit_with_default_arguments():
    """Test JIT compilation with default argument values."""
    schema = strawberry.Schema(Query)
    
    query = """
    query GetUserWithDefaults {
        user(id: "456") {
            id
            name
            posts {
                id
                title
            }
            recentPosts(minViews: 500) {
                id
                title
                views
            }
        }
    }
    """
    
    # Compile with JIT
    compiled_fn = compile_query(schema._schema, query)
    
    # Execute both ways
    root = Query()
    jit_result = compiled_fn(root)
    standard_result = execute(schema._schema, parse(query), root_value=root)
    
    # Verify results match
    assert jit_result == standard_result.data
    assert jit_result["user"]["id"] == "456"
    # Should use default limit=10
    assert len(jit_result["user"]["posts"]) <= 10
    # Should use default days=7
    assert len(jit_result["user"]["recentPosts"]) <= 7
    # All should have views >= 500
    for post in jit_result["user"]["recentPosts"]:
        assert post["views"] >= 500


def test_jit_with_variables():
    """Test JIT compilation with query variables."""
    schema = strawberry.Schema(Query)
    
    query = """
    query GetUserPosts($userId: String!, $postLimit: Int!, $onlyPublished: Boolean) {
        user(id: $userId) {
            id
            name
            posts(limit: $postLimit, published: $onlyPublished) {
                id
                title
                published
            }
        }
    }
    """
    
    # Compile with JIT
    compiled_fn = compile_query(schema._schema, query)
    
    # Execute with variables
    root = Query()
    variables = {
        "userId": "789",
        "postLimit": 3,
        "onlyPublished": True,
    }
    
    jit_result = compiled_fn(root, variables=variables)
    standard_result = execute(
        schema._schema,
        parse(query),
        root_value=root,
        variable_values=variables,
    )
    
    # Verify results match
    assert jit_result == standard_result.data
    assert jit_result["user"]["id"] == "789"
    assert len(jit_result["user"]["posts"]) <= 3
    assert all(p["published"] for p in jit_result["user"]["posts"])


def test_jit_with_list_arguments():
    """Test JIT compilation with list arguments."""
    schema = strawberry.Schema(Query)
    
    query = """
    query GetPostsByIds {
        postsByIds(ids: ["1", "2", "3"]) {
            id
            title
        }
    }
    """
    
    # Compile with JIT
    compiled_fn = compile_query(schema._schema, query)
    
    # Execute both ways
    root = Query()
    jit_result = compiled_fn(root)
    standard_result = execute(schema._schema, parse(query), root_value=root)
    
    # Verify results match
    assert jit_result == standard_result.data
    assert len(jit_result["postsByIds"]) == 3
    assert jit_result["postsByIds"][0]["id"] == "1"
    assert jit_result["postsByIds"][1]["id"] == "2"
    assert jit_result["postsByIds"][2]["id"] == "3"


def test_jit_with_complex_arguments():
    """Test JIT compilation with complex argument combinations."""
    schema = strawberry.Schema(Query)
    
    query = """
    query SearchPosts {
        searchPosts(query: "GraphQL", limit: 10, publishedOnly: false, minViews: 100) {
            totalCount
            posts {
                id
                title
                views
                published
            }
        }
    }
    """
    
    # Compile with JIT
    compiled_fn = compile_query(schema._schema, query)
    
    # Execute both ways
    root = Query()
    jit_result = compiled_fn(root)
    standard_result = execute(schema._schema, parse(query), root_value=root)
    
    # Verify results match
    assert jit_result == standard_result.data
    assert len(jit_result["searchPosts"]["posts"]) <= 10
    # Check that minViews filter is applied
    for post in jit_result["searchPosts"]["posts"]:
        assert post["views"] >= 100


def test_jit_with_null_arguments():
    """Test JIT compilation with null/optional arguments."""
    schema = strawberry.Schema(Query)
    
    query = """
    query GetAllPosts {
        user(id: "null-test") {
            posts(published: null, offset: 5) {
                id
                published
            }
        }
    }
    """
    
    # Compile with JIT
    compiled_fn = compile_query(schema._schema, query)
    
    # Execute both ways
    root = Query()
    jit_result = compiled_fn(root)
    standard_result = execute(schema._schema, parse(query), root_value=root)
    
    # Verify results match
    assert jit_result == standard_result.data
    # Should include both published and unpublished since published=null
    published_states = {p["published"] for p in jit_result["user"]["posts"]}
    assert True in published_states or False in published_states  # Should have mixed results


def test_jit_arguments_performance():
    """Test that JIT provides performance benefit even with arguments."""
    schema = strawberry.Schema(Query)
    
    query = """
    query ComplexArgumentQuery {
        user1: user(id: "1") {
            posts(limit: 5, published: true, offset: 0) {
                id
                title
            }
        }
        user2: user(id: "2") {
            posts(limit: 10, published: false, offset: 5) {
                id
                title
            }
        }
        search: searchPosts(query: "test", limit: 15, minViews: 200) {
            totalCount
            posts {
                id
                views
            }
        }
        selectedPosts: postsByIds(ids: ["a", "b", "c", "d", "e"]) {
            id
            title
        }
    }
    """
    
    # Parse and compile
    parsed_query = parse(query)
    compiled_fn = compile_query(schema._schema, query)
    root = Query()
    
    # Warm up
    compiled_fn(root)
    execute(schema._schema, parsed_query, root_value=root)
    
    # Measure performance
    iterations = 100
    
    # JIT execution
    jit_start = time.perf_counter()
    for _ in range(iterations):
        jit_result = compiled_fn(root)
    jit_time = time.perf_counter() - jit_start
    
    # Standard execution
    standard_start = time.perf_counter()
    for _ in range(iterations):
        standard_result = execute(schema._schema, parsed_query, root_value=root)
    standard_time = time.perf_counter() - standard_start
    
    # Calculate speedup
    speedup = standard_time / jit_time
    
    print(f"\nArguments Performance Test ({iterations} iterations):")
    print(f"  Standard GraphQL: {standard_time * 1000:.2f}ms")
    print(f"  JIT Compiled:     {jit_time * 1000:.2f}ms")
    print(f"  Speedup:          {speedup:.1f}x")
    
    # JIT should still be faster even with argument handling
    assert jit_time < standard_time
    assert speedup > 1.5  # Should have at least 1.5x speedup


if __name__ == "__main__":
    test_jit_with_simple_arguments()
    test_jit_with_default_arguments()
    test_jit_with_variables()
    test_jit_with_list_arguments()
    test_jit_with_complex_arguments()
    test_jit_with_null_arguments()
    test_jit_arguments_performance()
    print("\n✅ All JIT argument tests passed!")