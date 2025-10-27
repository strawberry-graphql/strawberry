"""
Test JIT compilation with field arguments support.
"""

import time
from typing import List, Optional

from graphql import execute, parse

import strawberry
from strawberry.jit import compile_query
from tests.jit.conftest import assert_jit_results_match


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
    def posts(
        self, published: Optional[bool] = None, limit: int = 10, offset: int = 0
    ) -> List[Post]:
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
        return filtered[offset : offset + limit]

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
            if published_only and i % 2 != 0:
                continue
            views = i * 100
            if min_views and views < min_views:
                continue
            if query.lower() not in f"Post {i}".lower():
                continue
            posts.append(
                Post(
                    id=f"search_{i}",
                    title=f"Post {i}",
                    content=f"Content matching {query}",
                    published=i % 2 == 0,
                    views=views,
                )
            )

        return SearchResult(posts=posts, total_count=len(posts))

    @strawberry.field
    def posts_by_ids(self, ids: List[str]) -> List[Post]:
        """Get posts by IDs."""
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

    # Execute the compiled function
    compiled_fn = compile_query(schema, query)
    root = Query()
    result = compiled_fn(root)

    # Verify results match
    standard_result = execute(schema._schema, parse(query), root_value=root)
    assert_jit_results_match(result, standard_result)
    assert result["data"]["user"]["id"] == "123"
    assert len(result["data"]["user"]["posts"]) <= 5
    assert all(p["published"] for p in result["data"]["user"]["posts"])


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

    # Execute both ways
    compiled_fn = compile_query(schema, query)
    root = Query()
    jit_result = compiled_fn(root)
    standard_result = execute(schema._schema, parse(query), root_value=root)

    # Verify results match
    assert_jit_results_match(jit_result, standard_result)
    assert jit_result["data"]["user"]["id"] == "456"
    # Should use default limit=10
    assert len(jit_result["data"]["user"]["posts"]) <= 10
    # Should use default days=7
    assert len(jit_result["data"]["user"]["recentPosts"]) <= 7
    # All should have views >= 500
    for post in jit_result["data"]["user"]["recentPosts"]:
        assert post["views"] >= 500


def test_jit_with_variables():
    """Test JIT compilation with GraphQL variables."""
    schema = strawberry.Schema(Query)

    query = """
    query GetUser($userId: String!, $postLimit: Int!, $onlyPublished: Boolean) {
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

    variables = {"userId": "789", "postLimit": 3, "onlyPublished": False}

    # Execute both ways
    compiled_fn = compile_query(schema, query)
    root = Query()
    jit_result = compiled_fn(root, variables=variables)
    standard_result = execute(
        schema._schema, parse(query), root_value=root, variable_values=variables
    )

    # Verify results match
    assert_jit_results_match(jit_result, standard_result)
    assert jit_result["data"]["user"]["id"] == "789"
    assert len(jit_result["data"]["user"]["posts"]) <= 3


def test_jit_with_list_arguments():
    """Test JIT compilation with list arguments."""
    schema = strawberry.Schema(Query)

    query = """
    query GetPostsByIds($ids: [String!]!) {
        postsByIds(ids: $ids) {
            id
            title
        }
    }
    """

    variables = {"ids": ["post1", "post2", "post3"]}

    # Execute both ways
    compiled_fn = compile_query(schema, query)
    root = Query()
    jit_result = compiled_fn(root, variables=variables)
    standard_result = execute(
        schema._schema, parse(query), root_value=root, variable_values=variables
    )

    # Verify results match
    assert_jit_results_match(jit_result, standard_result)
    assert len(jit_result["data"]["postsByIds"]) == 3
    assert [p["id"] for p in jit_result["data"]["postsByIds"]] == [
        "post1",
        "post2",
        "post3",
    ]


def test_jit_with_complex_arguments():
    """Test JIT compilation with complex argument combinations."""
    schema = strawberry.Schema(Query)

    query = """
    query SearchPosts($query: String!, $limit: Int, $minViews: Int) {
        searchPosts(query: $query, limit: $limit, minViews: $minViews) {
            posts {
                id
                title
                views
            }
            totalCount
        }
    }
    """

    variables = {"query": "Post", "limit": 10, "minViews": 200}

    # Execute both ways
    compiled_fn = compile_query(schema, query)
    root = Query()
    jit_result = compiled_fn(root, variables=variables)
    standard_result = execute(
        schema._schema, parse(query), root_value=root, variable_values=variables
    )

    # Verify results match
    assert_jit_results_match(jit_result, standard_result)
    if jit_result["data"]["searchPosts"]["posts"]:
        for post in jit_result["data"]["searchPosts"]["posts"]:
            assert post["views"] >= 200


def test_jit_with_null_arguments():
    """Test JIT compilation with null argument values."""
    schema = strawberry.Schema(Query)

    query = """
    query GetUserPosts($published: Boolean) {
        user(id: "999") {
            id
            posts(published: $published) {
                id
                published
            }
        }
    }
    """

    # Test with null (should return all posts)
    variables = {"published": None}

    compiled_fn = compile_query(schema, query)
    root = Query()
    jit_result = compiled_fn(root, variables=variables)
    standard_result = execute(
        schema._schema, parse(query), root_value=root, variable_values=variables
    )

    assert_jit_results_match(jit_result, standard_result)
    # Should return both published and unpublished
    published_count = sum(
        1 for p in jit_result["data"]["user"]["posts"] if p["published"]
    )
    unpublished_count = len(jit_result["data"]["user"]["posts"]) - published_count
    assert published_count > 0
    assert unpublished_count > 0


def test_jit_arguments_performance():
    """Test performance of JIT compilation with arguments."""
    schema = strawberry.Schema(Query)

    query = """
    query GetUser($userId: String!, $limit: Int!) {
        user(id: $userId) {
            id
            name
            posts(limit: $limit) {
                id
                title
            }
        }
    }
    """

    variables = {"userId": "perf_test", "limit": 5}

    # Compile once
    compiled_fn = compile_query(schema, query)
    root = Query()

    # Measure JIT performance
    jit_start = time.time()
    for _ in range(100):
        jit_result = compiled_fn(root, variables=variables)
    jit_time = time.time() - jit_start

    # Measure standard performance
    parsed_query = parse(query)
    standard_start = time.time()
    for _ in range(100):
        standard_result = execute(
            schema._schema, parsed_query, root_value=root, variable_values=variables
        )
    standard_time = time.time() - standard_start

    print(f"JIT time: {jit_time:.4f}s")
    print(f"Standard time: {standard_time:.4f}s")
    print(f"Speedup: {standard_time / jit_time:.2f}x")

    # JIT should be faster
    assert jit_time < standard_time


if __name__ == "__main__":
    test_jit_with_simple_arguments()
    test_jit_with_default_arguments()
    test_jit_with_variables()
    test_jit_with_list_arguments()
    test_jit_with_complex_arguments()
    test_jit_with_null_arguments()
    test_jit_arguments_performance()
    print("✅ All argument tests passed!")
