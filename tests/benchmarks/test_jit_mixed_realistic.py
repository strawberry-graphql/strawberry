"""Benchmark for realistic mixed async/sync queries.

This benchmark represents real-world GraphQL usage patterns:
- Top-level async fields (DB queries)
- Some nested async fields (relationship loading)
- Many sync fields (scalars, computed properties)

The goal is to test JIT performance on queries that mirror production workloads
where most fields are sync but critical data loading is async.
"""

import asyncio

import pytest
from pytest_codspeed.plugin import BenchmarkFixture

import strawberry
from strawberry.jit import compile_query


@strawberry.type
class Address:
    """All sync fields - basic data."""

    street: str
    city: str
    state: str
    zip_code: str
    country: str


@strawberry.type
class Profile:
    """Mix of sync and one async field."""

    bio: str
    avatar_url: str
    website: str
    twitter_handle: str
    github_username: str
    linkedin_url: str

    @strawberry.field
    async def followers_count(self) -> int:
        """Simulates async DB aggregation query."""
        await asyncio.sleep(0.0001)
        return 1234


@strawberry.type
class Post:
    """Many sync fields, one async nested."""

    id: str
    title: str
    slug: str
    excerpt: str
    published_at: str
    updated_at: str
    view_count: int
    like_count: int
    comment_count: int
    is_featured: bool
    is_published: bool
    tags: list[str]

    @strawberry.field
    async def author_name(self) -> str:
        """Simulates async lookup."""
        await asyncio.sleep(0.0001)
        return "John Doe"


@strawberry.type
class User:
    """Many sync fields, two async nested objects."""

    # Sync fields - majority of fields
    id: str
    username: str
    email: str
    first_name: str
    last_name: str
    display_name: str
    created_at: str
    updated_at: str
    last_login: str
    is_active: bool
    is_verified: bool
    is_staff: bool
    phone_number: str
    timezone: str
    locale: str

    @strawberry.field
    async def profile(self) -> Profile:
        """Async relationship load."""
        await asyncio.sleep(0.0001)
        return Profile(
            bio="Software developer",
            avatar_url="https://example.com/avatar.jpg",
            website="https://example.com",
            twitter_handle="@johndoe",
            github_username="johndoe",
            linkedin_url="https://linkedin.com/in/johndoe",
        )

    @strawberry.field
    async def address(self) -> Address:
        """Async relationship load."""
        await asyncio.sleep(0.0001)
        return Address(
            street="123 Main St",
            city="San Francisco",
            state="CA",
            zip_code="94102",
            country="USA",
        )


@strawberry.type
class Query:
    @strawberry.field
    async def users(self, limit: int = 20) -> list[User]:
        """Top-level async query."""
        await asyncio.sleep(0.0001)
        return [
            User(
                id=f"user_{i}",
                username=f"user{i}",
                email=f"user{i}@example.com",
                first_name=f"First{i}",
                last_name=f"Last{i}",
                display_name=f"User {i}",
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-15T00:00:00Z",
                last_login="2024-01-20T00:00:00Z",
                is_active=True,
                is_verified=i % 3 == 0,
                is_staff=i % 10 == 0,
                phone_number=f"+1-555-{i:04d}",
                timezone="America/Los_Angeles",
                locale="en_US",
            )
            for i in range(limit)
        ]

    @strawberry.field
    async def posts(self, limit: int = 50) -> list[Post]:
        """Top-level async query with many items."""
        await asyncio.sleep(0.0001)
        return [
            Post(
                id=f"post_{i}",
                title=f"Post Title {i}",
                slug=f"post-title-{i}",
                excerpt=f"This is an excerpt for post {i}...",
                published_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-15T00:00:00Z",
                view_count=i * 100,
                like_count=i * 10,
                comment_count=i * 5,
                is_featured=i % 5 == 0,
                is_published=i % 2 == 0,
                tags=[f"tag{j}" for j in range(3)],
            )
            for i in range(limit)
        ]


# Realistic query: top-level async, nested async, but LOTS of sync fields
REALISTIC_MIXED_QUERY = """
query RealisticWorkload {
    users(limit: 20) {
        id
        username
        email
        firstName
        lastName
        displayName
        createdAt
        updatedAt
        lastLogin
        isActive
        isVerified
        isStaff
        phoneNumber
        timezone
        locale
        profile {
            bio
            avatarUrl
            website
            twitterHandle
            githubUsername
            linkedinUrl
            followersCount
        }
        address {
            street
            city
            state
            zipCode
            country
        }
    }
    posts(limit: 50) {
        id
        title
        slug
        excerpt
        publishedAt
        updatedAt
        viewCount
        likeCount
        commentCount
        isFeatured
        isPublished
        tags
        authorName
    }
}
"""


@pytest.mark.benchmark
def test_jit_realistic_mixed(benchmark: BenchmarkFixture):
    """Benchmark JIT with realistic mixed async/sync workload.

    Pattern:
    - 2 top-level async queries (users, posts)
    - 20 users × (15 sync fields + 2 async nested objects with 6 sync fields each)
    - 50 posts × (12 sync fields + 1 async field)
    - Total: ~700 sync fields + ~70 async operations

    This mirrors real-world usage where:
    - Data loading is async (top-level + relationships)
    - Most fields are sync scalars (id, name, timestamps, flags, etc.)
    - GraphQL Core overhead is dominated by field serialization
    """
    schema = strawberry.Schema(query=Query)
    compiled_fn = compile_query(schema, REALISTIC_MIXED_QUERY)
    root = Query()

    def run():
        return asyncio.run(compiled_fn(root))

    result = benchmark(run)
    assert result["data"] is not None
    assert len(result["data"]["users"]) == 20
    assert len(result["data"]["posts"]) == 50


@pytest.mark.benchmark
def test_standard_realistic_mixed_baseline(benchmark: BenchmarkFixture):
    """Baseline for standard GraphQL with realistic mixed workload."""
    schema = strawberry.Schema(query=Query)
    root = Query()

    def run():
        return asyncio.run(schema.execute(REALISTIC_MIXED_QUERY, root_value=root))

    result = benchmark(run)
    assert result.errors is None
    assert result.data is not None
    assert len(result.data["users"]) == 20
    assert len(result.data["posts"]) == 50


# Variant: Fewer async, more sync fields (even more realistic)
MOSTLY_SYNC_QUERY = """
query MostlySyncWorkload {
    posts(limit: 100) {
        id
        title
        slug
        excerpt
        publishedAt
        updatedAt
        viewCount
        likeCount
        commentCount
        isFeatured
        isPublished
        tags
    }
}
"""


@pytest.mark.benchmark
def test_jit_mostly_sync_many_items(benchmark: BenchmarkFixture):
    """Benchmark JIT with mostly sync fields but many items.

    Pattern:
    - 1 top-level async query
    - 100 posts × 12 sync fields = 1200 scalar serializations
    - Only 1 async operation total

    This tests the overhead of GraphQL Core field resolution/serialization
    for large result sets with simple scalar fields.
    """
    schema = strawberry.Schema(query=Query)
    compiled_fn = compile_query(schema, MOSTLY_SYNC_QUERY)
    root = Query()

    def run():
        return asyncio.run(compiled_fn(root))

    result = benchmark(run)
    assert result["data"] is not None
    assert len(result["data"]["posts"]) == 100


@pytest.mark.benchmark
def test_standard_mostly_sync_many_items_baseline(benchmark: BenchmarkFixture):
    """Baseline for mostly sync with many items."""
    schema = strawberry.Schema(query=Query)
    root = Query()

    def run():
        return asyncio.run(schema.execute(MOSTLY_SYNC_QUERY, root_value=root))

    result = benchmark(run)
    assert result.errors is None
    assert result.data is not None
    assert len(result.data["posts"]) == 100
