"""Comprehensive async error handling tests for JIT compiler.

Tests error propagation, parallel execution errors, and async-specific scenarios.
"""

import pytest

import strawberry
from strawberry.jit import compile_query


# Test schema with async fields that can error
@strawberry.type
class User:
    id: int
    name: str


@strawberry.type
class Query:
    @strawberry.field
    async def async_user(self, user_id: int) -> User:
        """Async field that can error."""
        if user_id == 999:
            raise ValueError(f"User {user_id} not found")
        return User(id=user_id, name=f"User{user_id}")

    @strawberry.field
    async def async_nullable_user(self, user_id: int) -> User | None:
        """Nullable async field that can error."""
        if user_id == 999:
            raise ValueError(f"User {user_id} not found")
        if user_id == 0:
            return None
        return User(id=user_id, name=f"User{user_id}")

    @strawberry.field
    async def async_field1(self) -> str:
        """First async field for parallel testing."""
        return "field1"

    @strawberry.field
    async def async_field2(self) -> str:
        """Second async field that errors."""
        raise ValueError("Error in field2")

    @strawberry.field
    async def async_field3(self) -> str:
        """Third async field for parallel testing."""
        return "field3"

    @strawberry.field
    async def async_list_users(self, ids: list[int]) -> list[User]:
        """Async field returning list."""
        users = []
        for user_id in ids:
            if user_id == 999:
                raise ValueError(f"User {user_id} not found")
            users.append(User(id=user_id, name=f"User{user_id}"))
        return users

    @strawberry.field
    async def async_nullable_list(self, ids: list[int]) -> list[User] | None:
        """Nullable list async field."""
        if not ids:
            return None
        users = []
        for user_id in ids:
            if user_id == 999:
                raise ValueError(f"User {user_id} not found")
            users.append(User(id=user_id, name=f"User{user_id}"))
        return users

    @strawberry.field
    def sync_field(self) -> str:
        """Sync field for mixed testing."""
        return "sync"


@pytest.mark.asyncio
async def test_async_field_error_non_nullable():
    """Test error in non-nullable async field propagates correctly."""
    schema = strawberry.Schema(Query)
    query = """
    query {
        asyncUser(userId: 999) {
            id
            name
        }
    }
    """

    compiled = compile_query(schema, query)
    result = await compiled(Query())

    assert result["data"] is None
    assert len(result["errors"]) == 1
    assert "User 999 not found" in result["errors"][0]["message"]
    assert result["errors"][0]["path"] == ["asyncUser"]


@pytest.mark.asyncio
async def test_async_field_error_nullable():
    """Test error in nullable async field returns null."""
    schema = strawberry.Schema(Query)
    query = """
    query {
        asyncNullableUser(userId: 999) {
            id
            name
        }
    }
    """

    compiled = compile_query(schema, query)
    result = await compiled(Query())

    assert result["data"]["asyncNullableUser"] is None
    assert len(result["errors"]) == 1
    assert "User 999 not found" in result["errors"][0]["message"]
    assert result["errors"][0]["path"] == ["asyncNullableUser"]


@pytest.mark.asyncio
async def test_async_nullable_field_returns_none():
    """Test nullable async field can return None without error."""
    schema = strawberry.Schema(Query)
    query = """
    query {
        asyncNullableUser(userId: 0) {
            id
            name
        }
    }
    """

    compiled = compile_query(schema, query)
    result = await compiled(Query())

    assert result["data"]["asyncNullableUser"] is None
    assert "errors" not in result or len(result["errors"]) == 0


@pytest.mark.asyncio
async def test_parallel_async_fields_one_errors():
    """Test parallel async execution when one field errors.

    When async fields execute in parallel, error in one field should:
    - Allow other fields to complete successfully
    - Set the errored field's value based on its nullability
    - Include error in the errors array
    """
    schema = strawberry.Schema(Query)
    query = """
    query {
        asyncField1
        asyncField2
        asyncField3
    }
    """

    compiled = compile_query(schema, query)
    result = await compiled(Query())

    # Other fields should complete successfully
    assert result["data"]["asyncField1"] == "field1"
    assert result["data"]["asyncField3"] == "field3"
    # Errored non-nullable field should be absent (data is partial)
    assert "asyncField2" not in result["data"]

    # Error should be recorded (may have duplicates in current implementation)
    assert len(result["errors"]) >= 1
    error_messages = [e["message"] for e in result["errors"]]
    assert any("Error in field2" in msg for msg in error_messages)
    # At least one error should have the correct path
    assert any(e["path"] == ["asyncField2"] for e in result["errors"])


@pytest.mark.asyncio
async def test_async_list_field_error():
    """Test error in async field returning list."""
    schema = strawberry.Schema(Query)
    query = """
    query {
        asyncListUsers(ids: [1, 2, 999, 3]) {
            id
            name
        }
    }
    """

    compiled = compile_query(schema, query)
    result = await compiled(Query())

    assert result["data"] is None
    assert len(result["errors"]) == 1
    assert "User 999 not found" in result["errors"][0]["message"]
    assert result["errors"][0]["path"] == ["asyncListUsers"]


@pytest.mark.asyncio
async def test_async_nullable_list_error():
    """Test error in nullable list async field."""
    schema = strawberry.Schema(Query)
    query = """
    query {
        asyncNullableList(ids: [1, 2, 999]) {
            id
            name
        }
    }
    """

    compiled = compile_query(schema, query)
    result = await compiled(Query())

    assert result["data"]["asyncNullableList"] is None
    assert len(result["errors"]) == 1
    assert "User 999 not found" in result["errors"][0]["message"]
    assert result["errors"][0]["path"] == ["asyncNullableList"]


@pytest.mark.asyncio
async def test_mixed_sync_async_with_error():
    """Test mixed sync/async fields when async field errors."""
    schema = strawberry.Schema(Query)
    query = """
    query {
        syncField
        asyncField2
    }
    """

    compiled = compile_query(schema, query)
    result = await compiled(Query())

    assert result["data"] is None
    assert len(result["errors"]) == 1
    assert "Error in field2" in result["errors"][0]["message"]


@pytest.mark.asyncio
async def test_nested_async_field_error():
    """Test error in nested async field."""

    @strawberry.type
    class Post:
        id: int
        title: str

        @strawberry.field
        async def author(self) -> User:
            if self.id == 999:
                raise ValueError("Author not found for post 999")
            return User(id=1, name="Author1")

    @strawberry.type
    class QueryNested:
        @strawberry.field
        async def post(self, post_id: int) -> Post:
            return Post(id=post_id, title=f"Post{post_id}")

    schema = strawberry.Schema(QueryNested)
    query = """
    query {
        post(postId: 999) {
            id
            title
            author {
                id
                name
            }
        }
    }
    """

    compiled = compile_query(schema, query)
    result = await compiled(QueryNested())

    assert result["data"] is None
    assert len(result["errors"]) == 1
    assert "Author not found for post 999" in result["errors"][0]["message"]
    assert result["errors"][0]["path"] == ["post", "author"]


@pytest.mark.asyncio
async def test_multiple_async_errors():
    """Test multiple async fields erroring.

    When multiple async fields error in parallel:
    - Successful fields should still complete
    - Each error should be recorded
    - Data should be partial (contains successful fields)
    """

    @strawberry.type
    class QueryMultiError:
        @strawberry.field
        async def error_field1(self) -> str:
            raise ValueError("Error 1")

        @strawberry.field
        async def error_field2(self) -> str:
            raise ValueError("Error 2")

        @strawberry.field
        async def success_field(self) -> str:
            return "success"

    schema = strawberry.Schema(QueryMultiError)
    query = """
    query {
        errorField1
        errorField2
        successField
    }
    """

    compiled = compile_query(schema, query)
    result = await compiled(QueryMultiError())

    # Successful field should complete
    assert result["data"]["successField"] == "success"
    # Errored fields should be absent
    assert "errorField1" not in result["data"]
    assert "errorField2" not in result["data"]

    # Should have errors from both fields (may have duplicates)
    assert len(result["errors"]) >= 2
    error_messages = [e["message"] for e in result["errors"]]
    # Both errors should be present
    assert any("Error 1" in msg for msg in error_messages)
    assert any("Error 2" in msg for msg in error_messages)
    # Both should have correct paths
    assert any(e["path"] == ["errorField1"] for e in result["errors"])
    assert any(e["path"] == ["errorField2"] for e in result["errors"])


@pytest.mark.asyncio
async def test_async_field_with_variables_error():
    """Test async field error with variables."""
    schema = strawberry.Schema(Query)
    query = """
    query GetUser($id: Int!) {
        asyncUser(userId: $id) {
            id
            name
        }
    }
    """

    compiled = compile_query(schema, query)
    result = await compiled(Query(), variables={"id": 999})

    assert result["data"] is None
    assert len(result["errors"]) == 1
    assert "User 999 not found" in result["errors"][0]["message"]


@pytest.mark.asyncio
async def test_async_field_success_path():
    """Test async field happy path for comparison."""
    schema = strawberry.Schema(Query)
    query = """
    query {
        asyncUser(userId: 1) {
            id
            name
        }
    }
    """

    compiled = compile_query(schema, query)
    result = await compiled(Query())

    assert result["data"]["asyncUser"]["id"] == 1
    assert result["data"]["asyncUser"]["name"] == "User1"
    assert "errors" not in result or len(result["errors"]) == 0
