"""
Shared schema and fixtures for JIT compiler tests.
"""

import asyncio
import time
from enum import Enum
from typing import Annotated, Optional, Union

import pytest

import strawberry


# Enums
@strawberry.enum
class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@strawberry.enum
class PostStatus(Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


# Basic types
@strawberry.type
class Author:
    id: str
    name: str
    email: str
    verified: bool = False

    @strawberry.field
    def full_name(self) -> str:
        """Computed field."""
        return self.name

    @strawberry.field
    async def posts_count(self) -> int:
        """Async field simulating database query."""
        await asyncio.sleep(0.001)
        return 5

    @strawberry.field
    async def bio(self, delay: float = 0) -> str:
        """Async field with optional delay."""
        if delay > 0:
            await asyncio.sleep(delay)
        return f"Bio of {self.name}"


@strawberry.type
class Comment:
    id: str
    text: str
    author: Author
    created_at: Optional[float] = None

    @strawberry.field
    async def likes(self) -> int:
        """Async field for comment likes."""
        await asyncio.sleep(0.001)
        return 42


@strawberry.type
class Post:
    id: str
    title: str
    content: str
    author: Author
    published: bool = False
    status: PostStatus = PostStatus.DRAFT
    priority: Optional[Priority] = None
    views: int = 0
    tags: list[str] = strawberry.field(default_factory=list)
    comments: list[Comment] = strawberry.field(default_factory=list)

    @strawberry.field
    async def view_count(self) -> int:
        """Async field simulating database query."""
        await asyncio.sleep(0.001)
        return self.views

    @strawberry.field
    def sync_author(self) -> Author:
        """Sync field returning author."""
        return self.author

    @strawberry.field
    async def async_comments(self, limit: int = 10) -> list[Comment]:
        """Async field returning comments."""
        await asyncio.sleep(0.001)
        return self.comments[:limit]


@strawberry.type
class User:
    id: str
    username: str
    email: str
    age: Optional[int] = None
    is_active: bool = True
    created_at: float = strawberry.field(default_factory=time.time)

    @strawberry.field
    def posts(self, limit: int = 10) -> list[Post]:
        """Get user's posts."""
        author = Author(id=self.id, name=self.username, email=self.email)
        return [
            Post(
                id=f"p{i}",
                title=f"Post {i} by {self.username}",
                content=f"Content {i}",
                author=author,
                published=i % 2 == 0,
                views=i * 100,
            )
            for i in range(limit)
        ]


# Union type for testing
@strawberry.type
class Article:
    id: str
    title: str
    content: str
    author: Author


@strawberry.type
class Video:
    id: str
    title: str
    url: str
    duration: int
    author: Author


@strawberry.type
class Image:
    id: str
    title: str
    url: str
    width: int
    height: int
    author: Author


SearchResult = Annotated[Union[Article, Video, Image], strawberry.union("SearchResult")]


# Input types
@strawberry.input
class CreatePostInput:
    title: str
    content: str
    author_id: str
    published: bool = False
    priority: Optional[Priority] = None


@strawberry.input
class UpdatePostInput:
    id: str
    title: Optional[str] = strawberry.UNSET
    content: Optional[str] = strawberry.UNSET
    published: Optional[bool] = strawberry.UNSET


@strawberry.input
class FilterInput:
    keyword: Optional[str] = None
    published: Optional[bool] = None
    limit: int = 10


@strawberry.input
class NestedInput:
    filter: FilterInput
    sort_order: str = "asc"


# Mutation result types
@strawberry.type
class MutationResult:
    success: bool
    message: str
    code: Optional[int] = None


@strawberry.type
class PostMutationResult:
    post: Optional[Post]
    success: bool
    message: str


# Database simulator for mutations
class Database:
    """Simple in-memory database for testing mutations."""

    def __init__(self):
        self.users = {}
        self.posts = {}
        self.mutation_log = []
        self.counter = 0

    def reset(self):
        """Reset the database."""
        self.users.clear()
        self.posts.clear()
        self.mutation_log.clear()
        self.counter = 0

    def log_mutation(self, name: str):
        """Log a mutation for serial execution testing."""
        self.mutation_log.append((name, time.time()))

    def next_id(self) -> str:
        """Get next ID."""
        self.counter += 1
        return str(self.counter)


# Global database instance for tests
db = Database()


# Mutations
@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_post(self, input: CreatePostInput) -> PostMutationResult:
        """Create a new post."""
        db.log_mutation("create_post")

        post_id = db.next_id()
        author = Author(
            id=input.author_id,
            name=f"Author {input.author_id}",
            email=f"author{input.author_id}@example.com",
        )

        post = Post(
            id=post_id,
            title=input.title,
            content=input.content,
            author=author,
            published=input.published,
            priority=input.priority,
        )

        db.posts[post_id] = post

        return PostMutationResult(
            post=post,
            success=True,
            message=f"Post {post_id} created successfully",
        )

    @strawberry.mutation
    def update_post(self, input: UpdatePostInput) -> PostMutationResult:
        """Update an existing post."""
        db.log_mutation("update_post")

        if input.id not in db.posts:
            return PostMutationResult(
                post=None,
                success=False,
                message=f"Post {input.id} not found",
            )

        post = db.posts[input.id]

        if input.title is not strawberry.UNSET and input.title is not None:
            post.title = input.title
        if input.content is not strawberry.UNSET and input.content is not None:
            post.content = input.content
        if input.published is not strawberry.UNSET and input.published is not None:
            post.published = input.published

        return PostMutationResult(
            post=post,
            success=True,
            message=f"Post {input.id} updated successfully",
        )

    @strawberry.mutation
    def delete_post(self, id: str) -> MutationResult:
        """Delete a post."""
        db.log_mutation("delete_post")

        if id in db.posts:
            del db.posts[id]
            return MutationResult(
                success=True,
                message=f"Post {id} deleted successfully",
                code=200,
            )

        return MutationResult(
            success=False,
            message=f"Post {id} not found",
            code=404,
        )

    @strawberry.mutation
    async def async_mutation(self, delay: float = 0.001) -> MutationResult:
        """Async mutation for testing."""
        db.log_mutation("async_mutation")
        await asyncio.sleep(delay)
        return MutationResult(
            success=True,
            message="Async mutation completed",
            code=200,
        )


# Query type
@strawberry.type
class Query:
    @strawberry.field
    def posts(
        self,
        limit: int = 10,
        published: Optional[bool] = None,
        priority: Optional[Priority] = None,
    ) -> list[Post]:
        """Get posts with optional filtering."""
        authors = [
            Author(id="a1", name="Alice", email="alice@example.com", verified=True),
            Author(id="a2", name="Bob", email="bob@example.com", verified=False),
        ]

        posts = []
        for i in range(limit):
            post = Post(
                id=f"p{i}",
                title=f"Post {i}",
                content=f"Content for post {i}",
                author=authors[i % 2],
                published=i % 2 == 0,
                status=PostStatus.PUBLISHED if i % 2 == 0 else PostStatus.DRAFT,
                priority=Priority.HIGH if i % 3 == 0 else Priority.MEDIUM,
                views=i * 100,
                tags=[f"tag{j}" for j in range(i % 3)],
                comments=[
                    Comment(
                        id=f"c{i}-{j}",
                        text=f"Comment {j} on post {i}",
                        author=authors[j % 2],
                    )
                    for j in range(min(2, i))
                ],
            )

            # Apply filters
            if published is not None and post.published != published:
                continue
            if priority is not None and post.priority != priority:
                continue

            posts.append(post)

        return posts

    @strawberry.field
    async def async_posts(self, limit: int = 10) -> list[Post]:
        """Async version of posts query."""
        await asyncio.sleep(0.001)
        return self.posts(limit=limit)

    @strawberry.field
    def users(self, limit: int = 10) -> list[User]:
        """Get users."""
        return [
            User(
                id=f"u{i}",
                username=f"user{i}",
                email=f"user{i}@example.com",
                age=20 + i,
            )
            for i in range(limit)
        ]

    @strawberry.field
    async def async_users(self, limit: int = 10) -> list[User]:
        """Async version of users query."""
        await asyncio.sleep(0.001)
        return self.users(limit=limit)

    @strawberry.field
    async def async_comments(self, limit: int = 10) -> list[Comment]:
        """Async comments query for parallel execution testing."""
        await asyncio.sleep(0.001)
        alice = Author(id="a1", name="Alice", email="alice@example.com")
        return [
            Comment(
                id=f"c{i}",
                text=f"Comment {i}",
                author=alice,
            )
            for i in range(limit)
        ]

    @strawberry.field
    def post(self, id: str) -> Optional[Post]:
        """Get a single post by ID."""
        if id in db.posts:
            return db.posts[id]

        # Return a default post for testing
        return Post(
            id=id,
            title=f"Post {id}",
            content=f"Content for post {id}",
            author=Author(id="a1", name="Alice", email="alice@example.com"),
            published=True,
        )

    @strawberry.field
    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Search for content across different types."""
        results: list[SearchResult] = []
        author = Author(id="a1", name="Alice", email="alice@example.com")

        for i in range(limit):
            if i % 3 == 0:
                results.append(
                    Article(
                        id=f"article{i}",
                        title=f"Article matching {query}",
                        content=f"Content about {query}",
                        author=author,
                    )
                )
            elif i % 3 == 1:
                results.append(
                    Video(
                        id=f"video{i}",
                        title=f"Video about {query}",
                        url=f"https://example.com/video{i}",
                        duration=300 + i * 10,
                        author=author,
                    )
                )
            else:
                results.append(
                    Image(
                        id=f"image{i}",
                        title=f"Image of {query}",
                        url=f"https://example.com/image{i}.jpg",
                        width=1920,
                        height=1080,
                        author=author,
                    )
                )

        return results

    @strawberry.field
    def hello(self, name: str = "world") -> str:
        """Simple hello field."""
        return f"Hello {name}"

    @strawberry.field
    async def async_hello(self, name: str = "world") -> str:
        """Async hello field."""
        await asyncio.sleep(0.001)
        return f"Hello {name}"

    @strawberry.field
    def featured_post(self) -> Post:
        """Get the featured post."""
        return Post(
            id="featured",
            title="Featured Post",
            content="This is the featured post",
            author=Author(
                id="a1", name="Alice", email="alice@example.com", verified=True
            ),
            published=True,
            status=PostStatus.PUBLISHED,
            priority=Priority.HIGH,
            views=1000,
        )


# Create schema
schema = strawberry.Schema(query=Query, mutation=Mutation)


# Fixtures
@pytest.fixture
def jit_schema():
    """Get the JIT test schema."""
    return schema


@pytest.fixture
def query_type():
    """Get an instance of the Query type."""
    return Query()


@pytest.fixture
def clean_db():
    """Reset the database before each test."""
    db.reset()
    yield db
    db.reset()


@pytest.fixture
def sample_authors():
    """Get sample authors for testing."""
    return [
        Author(id="a1", name="Alice", email="alice@example.com", verified=True),
        Author(id="a2", name="Bob", email="bob@example.com", verified=False),
        Author(id="a3", name="Charlie", email="charlie@example.com", verified=True),
    ]


@pytest.fixture
def sample_posts(sample_authors):
    """Get sample posts for testing."""
    posts = []
    for i in range(5):
        posts.append(
            Post(
                id=f"p{i}",
                title=f"Post {i}",
                content=f"Content for post {i}",
                author=sample_authors[i % len(sample_authors)],
                published=i % 2 == 0,
                status=PostStatus.PUBLISHED if i % 2 == 0 else PostStatus.DRAFT,
                priority=Priority.HIGH if i == 0 else Priority.MEDIUM,
                views=i * 100,
                tags=[f"tag{j}" for j in range(i % 3)],
            )
        )
    return posts


def assert_jit_results_match(jit_result, standard_result):
    """
    Helper to compare JIT and standard execution results.
    Handles the data wrapper format correctly.
    """
    # Get JIT data - it's wrapped in {"data": ...}
    if isinstance(jit_result, dict) and "data" in jit_result:
        jit_data = jit_result["data"]
        jit_errors = jit_result.get("errors", [])
    else:
        # Fallback for older format
        jit_data = jit_result
        jit_errors = []

    # Get standard data
    std_data = (
        standard_result.data if hasattr(standard_result, "data") else standard_result
    )
    std_errors = standard_result.errors if hasattr(standard_result, "errors") else []
    std_errors = std_errors or []

    # Compare data
    assert jit_data == std_data, (
        f"Data mismatch:\nJIT: {jit_data}\nStandard: {std_data}"
    )

    # Compare errors
    assert len(jit_errors) == len(std_errors), (
        f"Error count mismatch:\nJIT: {len(jit_errors)} errors\n"
        f"Standard: {len(std_errors)} errors"
    )
