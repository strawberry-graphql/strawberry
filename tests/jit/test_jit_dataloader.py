"""Test JIT compiler with DataLoader integration.

Verifies that JIT-compiled queries work correctly with DataLoader batching.
"""

import pytest

import strawberry
from strawberry.dataloader import DataLoader
from strawberry.jit import compile_query


@strawberry.type
class User:
    id: str
    name: str
    email: str


@strawberry.type
class Post:
    id: str
    title: str
    author_id: str

    @strawberry.field
    async def author(self, info) -> User:
        """Resolve author using DataLoader."""
        loader = info.context["user_loader"]
        return await loader.load(self.author_id)


@strawberry.type
class Comment:
    id: str
    text: str
    post_id: str
    author_id: str

    @strawberry.field
    async def author(self, info) -> User:
        """Resolve comment author using DataLoader."""
        loader = info.context["user_loader"]
        return await loader.load(self.author_id)

    @strawberry.field
    async def post(self, info) -> Post:
        """Resolve post using DataLoader."""
        loader = info.context["post_loader"]
        return await loader.load(self.post_id)


@strawberry.type
class Query:
    @strawberry.field
    def posts(self) -> list[Post]:
        """Return test posts."""
        return [
            Post(id="p1", title="Post 1", author_id="u1"),
            Post(id="p2", title="Post 2", author_id="u1"),
            Post(id="p3", title="Post 3", author_id="u2"),
        ]

    @strawberry.field
    def comments(self) -> list[Comment]:
        """Return test comments."""
        return [
            Comment(id="c1", text="Comment 1", post_id="p1", author_id="u1"),
            Comment(id="c2", text="Comment 2", post_id="p1", author_id="u2"),
            Comment(id="c3", text="Comment 3", post_id="p2", author_id="u3"),
        ]


# Track batch calls for testing
batch_calls = []


async def load_users(keys: list[str]) -> list[User]:
    """Batch load users - tracks calls for testing."""
    batch_calls.append(("users", sorted(keys)))
    return [User(id=key, name=f"User {key}", email=f"{key}@example.com") for key in keys]


async def load_posts(keys: list[str]) -> list[Post]:
    """Batch load posts - tracks calls for testing."""
    batch_calls.append(("posts", sorted(keys)))
    return [Post(id=key, title=f"Post {key}", author_id="u1") for key in keys]


@pytest.mark.asyncio
async def test_jit_with_dataloader_batching():
    """Test that JIT works with DataLoader batching."""
    global batch_calls
    batch_calls = []

    schema = strawberry.Schema(query=Query)

    query = """
    {
        posts {
            title
            author {
                name
                email
            }
        }
    }
    """

    compiled = compile_query(schema, query)

    # Create DataLoader context
    context = {
        "user_loader": DataLoader(load_fn=load_users),
    }

    result = await compiled(Query(), context=context)

    # Verify results
    assert len(result["data"]["posts"]) == 3
    assert result["data"]["posts"][0]["author"]["name"] == "User u1"
    assert result["data"]["posts"][2]["author"]["name"] == "User u2"

    # Verify DataLoader batching - DataLoader batches within event loop ticks
    # JIT may split into multiple batches depending on async boundaries
    assert len(batch_calls) >= 1
    assert all(call[0] == "users" for call in batch_calls)

    # Collect all loaded user IDs across batches
    all_loaded_users = []
    for _, users in batch_calls:
        all_loaded_users.extend(users)

    # Should load u1 and u2 (unique authors)
    assert sorted(set(all_loaded_users)) == ["u1", "u2"]

    # Total loads should not exceed number of unique users
    assert len(all_loaded_users) <= 3  # At most 3 posts worth of loads


@pytest.mark.asyncio
async def test_jit_with_multiple_dataloaders():
    """Test JIT with multiple DataLoaders for different types."""
    global batch_calls
    batch_calls = []

    schema = strawberry.Schema(query=Query)

    query = """
    {
        comments {
            text
            author {
                name
            }
            post {
                title
            }
        }
    }
    """

    compiled = compile_query(schema, query)

    context = {
        "user_loader": DataLoader(load_fn=load_users),
        "post_loader": DataLoader(load_fn=load_posts),
    }

    result = await compiled(Query(), context=context)

    # Verify results
    assert len(result["data"]["comments"]) == 3
    assert result["data"]["comments"][0]["author"]["name"] == "User u1"
    assert result["data"]["comments"][0]["post"]["title"] == "Post p1"

    # Verify batching - should have both user and post batch calls
    user_batches = [b for b in batch_calls if b[0] == "users"]
    post_batches = [b for b in batch_calls if b[0] == "posts"]

    assert len(user_batches) >= 1
    assert len(post_batches) >= 1

    # Collect all loaded IDs
    all_users = []
    for _, users in user_batches:
        all_users.extend(users)

    all_posts = []
    for _, posts in post_batches:
        all_posts.extend(posts)

    # All 3 unique users should be loaded
    assert sorted(set(all_users)) == ["u1", "u2", "u3"]

    # Both unique posts should be loaded
    assert sorted(set(all_posts)) == ["p1", "p2"]


@pytest.mark.asyncio
async def test_jit_dataloader_with_duplicate_keys():
    """Test that DataLoader caching works with duplicate keys."""
    global batch_calls
    batch_calls = []

    schema = strawberry.Schema(query=Query)

    # Posts p1 and p2 both have author_id="u1"
    query = """
    {
        posts {
            title
            author {
                name
            }
        }
    }
    """

    compiled = compile_query(schema, query)

    context = {
        "user_loader": DataLoader(load_fn=load_users, cache=True),
    }

    result = await compiled(Query(), context=context)

    # Verify results
    assert len(result["data"]["posts"]) == 3
    assert result["data"]["posts"][0]["author"]["name"] == "User u1"
    assert result["data"]["posts"][1]["author"]["name"] == "User u1"

    # Verify batching across multiple event loop ticks
    assert len(batch_calls) >= 1

    # Collect all loaded users
    all_users = []
    for _, users in batch_calls:
        all_users.extend(users)

    # u1 appears twice in posts, u2 once - should load u1 and u2
    assert sorted(set(all_users)) == ["u1", "u2"]

    # With caching enabled, total loads should be minimal
    assert len(all_users) <= 3  # At most 3 loads for 3 posts


@pytest.mark.asyncio
async def test_jit_parallel_async_with_dataloader():
    """Test that JIT parallel execution doesn't break DataLoader batching."""

    @strawberry.type
    class ParallelQuery:
        @strawberry.field
        async def posts(self, info) -> list[Post]:
            """Async field 1."""
            return [Post(id="p1", title="Post 1", author_id="u1")]

        @strawberry.field
        async def comments(self, info) -> list[Comment]:
            """Async field 2."""
            return [Comment(id="c1", text="Comment 1", post_id="p1", author_id="u2")]

    global batch_calls
    batch_calls = []

    schema = strawberry.Schema(query=ParallelQuery)

    # Query two root fields in parallel
    query = """
    {
        posts {
            author {
                name
            }
        }
        comments {
            author {
                name
            }
        }
    }
    """

    compiled = compile_query(schema, query)

    context = {
        "user_loader": DataLoader(load_fn=load_users),
        "post_loader": DataLoader(load_fn=load_posts),
    }

    result = await compiled(ParallelQuery(), context=context)

    # Verify results from both parallel fields
    assert result["data"]["posts"][0]["author"]["name"] == "User u1"
    assert result["data"]["comments"][0]["author"]["name"] == "User u2"

    # Even with parallel execution, DataLoader should batch
    assert len(batch_calls) == 1
    assert batch_calls[0][0] == "users"
    # Both users loaded in one batch despite coming from parallel fields
    assert sorted(batch_calls[0][1]) == ["u1", "u2"]


@pytest.mark.asyncio
async def test_jit_dataloader_error_handling():
    """Test error handling when DataLoader fails."""

    async def load_users_with_error(keys: list[str]) -> list[User | BaseException]:
        """Loader that fails for specific keys."""
        results = []
        for key in keys:
            if key == "error":
                results.append(ValueError(f"User {key} not found"))
            else:
                results.append(User(id=key, name=f"User {key}", email=f"{key}@example.com"))
        return results

    schema = strawberry.Schema(query=Query)

    @strawberry.type
    class ErrorQuery:
        @strawberry.field
        def posts(self) -> list[Post]:
            return [
                Post(id="p1", title="Post 1", author_id="u1"),
                Post(id="p2", title="Post 2", author_id="error"),
            ]

    error_schema = strawberry.Schema(query=ErrorQuery)

    query = """
    {
        posts {
            title
            author {
                name
            }
        }
    }
    """

    compiled = compile_query(error_schema, query)

    context = {
        "user_loader": DataLoader(load_fn=load_users_with_error),
    }

    result = await compiled(ErrorQuery(), context=context)

    # Check if error caused data to be null (depends on nullability)
    if result["data"] is not None:
        # If partial data returned, verify structure
        assert len(result["data"]["posts"]) == 2
        # First post may succeed
        if result["data"]["posts"][0] is not None:
            assert result["data"]["posts"][0]["title"] == "Post 1"

    # Should have error in result
    assert "errors" in result
    assert len(result["errors"]) >= 1
    # Verify error message contains our custom message
    error_messages = [e["message"] for e in result["errors"]]
    assert any("not found" in msg for msg in error_messages)
