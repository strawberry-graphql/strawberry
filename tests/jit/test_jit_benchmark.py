"""
Benchmark tests for the GraphQL JIT compiler with large datasets.
"""

import random
import time

from graphql import execute, parse

import strawberry
from strawberry.jit import compile_query


@strawberry.type
class Comment:
    id: int
    text: str
    likes: int

    @strawberry.field
    def sentiment_score(self) -> float:
        """Custom resolver that calculates sentiment."""
        # Simulate some computation
        return len(self.text) * 0.1 + self.likes * 0.5


@strawberry.type
class Author:
    id: int
    name: str
    verified: bool
    followers: int

    @strawberry.field
    def reputation_score(self) -> int:
        """Custom resolver for reputation."""
        return self.followers * (10 if self.verified else 1)


@strawberry.type
class Post:
    id: int
    title: str
    content: str
    views: int
    author: Author
    comments: list[Comment]

    @strawberry.field
    def engagement_rate(self) -> float:
        """Custom resolver that calculates engagement."""
        return (len(self.comments) * 10 + self.views) / 100.0

    @strawberry.field
    def trending_score(self) -> float:
        """Complex calculation for trending."""
        base_score = self.views * 0.1
        comment_boost = len(self.comments) * 5
        author_boost = self.author.followers * 0.01
        return base_score + comment_boost + author_boost


def generate_large_dataset(num_posts: int, comments_per_post: int):
    """Generate a large dataset for benchmarking."""
    authors = [
        Author(
            id=i,
            name=f"Author_{i}",
            verified=i % 3 == 0,
            followers=random.randint(100, 100000),
        )
        for i in range(max(10, num_posts // 10))
    ]

    posts = []
    for i in range(num_posts):
        author = authors[i % len(authors)]
        comments = [
            Comment(
                id=j,
                text=f"Comment {j} on post {i} with some longer text to make it realistic",
                likes=random.randint(0, 1000),
            )
            for j in range(comments_per_post)
        ]
        posts.append(
            Post(
                id=i,
                title=f"Post {i}: An interesting title about topic {i % 20}",
                content=f"This is the content of post {i}. " * 10,  # Longer content
                views=random.randint(100, 1000000),
                author=author,
                comments=comments,
            )
        )
    return posts


@strawberry.type
class Query:
    posts_data: list[Post]

    def __init__(self, posts_data):
        self.posts_data = posts_data

    @strawberry.field
    def posts(self) -> list[Post]:
        return self.posts_data

    @strawberry.field
    def trending_posts(self) -> list[Post]:
        # This would normally query a database
        return sorted(self.posts_data, key=lambda p: p.trending_score(), reverse=True)[
            :10
        ]


def test_jit_with_small_dataset():
    """Test JIT performance with a small dataset."""
    posts_data = generate_large_dataset(num_posts=10, comments_per_post=5)
    schema = strawberry.Schema(Query)

    query = """
    query {
        posts {
            id
            title
            engagementRate
            author {
                name
                reputationScore
            }
            comments {
                text
                sentimentScore
            }
        }
    }
    """

    # Compile and execute
    compiled_fn = compile_query(schema, query)
    root = Query(posts_data)
    result = compiled_fn(root)

    # Verify we got results
    assert "data" in result
    assert "posts" in result["data"]
    assert len(result["data"]["posts"]) == 10
    assert "engagementRate" in result["data"]["posts"][0]
    assert "reputationScore" in result["data"]["posts"][0]["author"]


def test_jit_with_large_dataset():
    """Test JIT performance with a large dataset."""
    posts_data = generate_large_dataset(num_posts=500, comments_per_post=10)
    schema = strawberry.Schema(Query)

    query = """
    query {
        posts {
            id
            title
            views
            engagementRate
            trendingScore
            author {
                name
                verified
                reputationScore
            }
            comments {
                id
                text
                likes
                sentimentScore
            }
        }
    }
    """

    # Parse once for both
    parsed_query = parse(query)
    root = Query(posts_data)

    # Compile the query
    compiled_fn = compile_query(schema, query)

    # Warm up
    compiled_fn(root)
    execute(schema._schema, parsed_query, root_value=root)

    # Measure JIT execution
    iterations = 10
    start = time.perf_counter()
    for _ in range(iterations):
        jit_result = compiled_fn(root)
    jit_time = time.perf_counter() - start

    # Measure standard execution
    start = time.perf_counter()
    for _ in range(iterations):
        standard_result = execute(schema._schema, parsed_query, root_value=root)
    standard_time = time.perf_counter() - start

    speedup = standard_time / jit_time

    # Verify results match
    assert (
        jit_result["data"]["posts"][0]["id"] == standard_result.data["posts"][0]["id"]
    )
    assert len(jit_result["data"]["posts"]) == len(posts_data)

    # Assert significant speedup with large dataset
    assert speedup > 1.5, f"Expected speedup > 1.5x, got {speedup:.1f}x"


def test_jit_benchmark_comparison():
    """Comprehensive benchmark comparing different dataset sizes."""
    schema = strawberry.Schema(Query)

    # Complex query with multiple custom resolvers
    query = """
    query {
        posts {
            id
            title
            content
            views
            engagementRate
            trendingScore
            author {
                id
                name
                verified
                followers
                reputationScore
            }
            comments {
                id
                text
                likes
                sentimentScore
            }
        }
    }
    """

    parsed_query = parse(query)
    compiled_fn = compile_query(schema, query)

    dataset_configs = [
        (10, 5, 100),  # 10 posts, 5 comments each, 100 iterations
        (100, 10, 50),  # 100 posts, 10 comments each, 50 iterations
        (1000, 20, 5),  # 1000 posts, 20 comments each, 5 iterations
    ]

    for num_posts, comments_per_post, iterations in dataset_configs:
        posts_data = generate_large_dataset(num_posts, comments_per_post)
        root = Query(posts_data)

        total_items = num_posts * (1 + comments_per_post)  # posts + all comments

        # Warm up
        compiled_fn(root)
        execute(schema._schema, parsed_query, root_value=root)

        # Measure JIT
        start = time.perf_counter()
        for _ in range(iterations):
            compiled_fn(root)
        jit_time = time.perf_counter() - start

        # Measure standard
        start = time.perf_counter()
        for _ in range(iterations):
            execute(schema._schema, parsed_query, root_value=root)
        standard_time = time.perf_counter() - start

        standard_time / jit_time
        (total_items * iterations) / jit_time
        (total_items * iterations) / standard_time


def test_jit_with_minimal_fields():
    """Test that JIT provides maximum benefit when fetching minimal fields."""
    posts_data = generate_large_dataset(num_posts=1000, comments_per_post=10)
    schema = strawberry.Schema(Query)

    # Simple query - just IDs and titles
    query = """
    query {
        posts {
            id
            title
        }
    }
    """

    parsed_query = parse(query)
    compiled_fn = compile_query(schema, query)
    root = Query(posts_data)

    iterations = 100

    # Measure JIT
    start = time.perf_counter()
    for _ in range(iterations):
        compiled_fn(root)
    jit_time = time.perf_counter() - start

    # Measure standard
    start = time.perf_counter()
    for _ in range(iterations):
        execute(schema._schema, parsed_query, root_value=root)
    standard_time = time.perf_counter() - start

    speedup = standard_time / jit_time

    # With minimal fields, JIT should show even better performance
    assert speedup > 2.0, (
        f"Expected speedup > 2x for minimal fields, got {speedup:.1f}x"
    )


if __name__ == "__main__":
    # Run benchmarks directly
    test_jit_with_small_dataset()
    test_jit_with_large_dataset()
    test_jit_with_minimal_fields()
    test_jit_benchmark_comparison()
