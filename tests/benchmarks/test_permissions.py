"""Benchmark tests for permissions to ensure performance doesn't regress."""

import asyncio
from typing import Any, Literal

import pytest
from pytest_codspeed.plugin import BenchmarkFixture

import strawberry
from strawberry import Info
from strawberry.permission import BasePermission, PermissionExtension


# Test Permissions
class SyncPermissionAlwaysTrue(BasePermission):
    """Simple sync permission that always returns True."""

    def has_permission(self, source: Any, info: Info, **kwargs: object) -> bool:
        return True


class SyncPermissionAlwaysFalse(BasePermission):
    """Simple sync permission that always returns False."""

    def has_permission(self, source: Any, info: Info, **kwargs: object) -> bool:
        return False


class SyncPermissionWithContext(BasePermission):
    """Sync permission that returns False with context."""

    def has_permission(
        self, source: Any, info: Info, **kwargs: object
    ) -> tuple[Literal[False], dict]:
        return False, {"reason": "unauthorized"}


class AsyncPermissionAlwaysTrue(BasePermission):
    """Async permission that always returns True."""

    async def has_permission(self, source: Any, info: Info, **kwargs: object) -> bool:
        await asyncio.sleep(0.00001)  # Minimal async operation
        return True


class AsyncPermissionAlwaysFalse(BasePermission):
    """Async permission that always returns False."""

    async def has_permission(self, source: Any, info: Info, **kwargs: object) -> bool:
        await asyncio.sleep(0.00001)  # Minimal async operation
        return False


class UserBasedPermission(BasePermission):
    """Realistic permission checking user authentication."""

    def has_permission(self, source: Any, info: Info, **kwargs: object) -> bool:
        user = info.context.get("user", {})
        return user.get("is_authenticated", False)


class RoleBasedPermission(BasePermission):
    """Realistic permission checking user role."""

    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def has_permission(self, source: Any, info: Info, **kwargs: object) -> bool:
        user = info.context.get("user", {})
        return user.get("role") in self.allowed_roles


@pytest.mark.benchmark
def test_sync_permission_basic(benchmark: BenchmarkFixture):
    """Benchmark basic synchronous permission checks."""

    @strawberry.type
    class Query:
        @strawberry.field(
            extensions=[PermissionExtension(permissions=[SyncPermissionAlwaysTrue()])]
        )
        def protected_field(self) -> str:
            return "data"

    schema = strawberry.Schema(query=Query)
    query = "{ protectedField }"

    @benchmark
    def execute():
        result = schema.execute_sync(
            query, context_value={"user": {"is_authenticated": True}}
        )
        assert result.errors is None
        return result


@pytest.mark.benchmark
def test_async_permission_basic(benchmark: BenchmarkFixture):
    """Benchmark basic asynchronous permission checks."""

    @strawberry.type
    class Query:
        @strawberry.field(
            extensions=[PermissionExtension(permissions=[AsyncPermissionAlwaysTrue()])]
        )
        def protected_field(self) -> str:
            return "data"

    schema = strawberry.Schema(query=Query)
    query = "{ protectedField }"

    @benchmark
    def execute():
        result = asyncio.run(
            schema.execute(query, context_value={"user": {"is_authenticated": True}})
        )
        assert result.errors is None
        return result


@pytest.mark.benchmark
def test_and_permission_all_sync(benchmark: BenchmarkFixture):
    """Benchmark AND permissions with all synchronous checks."""

    perm1 = SyncPermissionAlwaysTrue()
    perm2 = UserBasedPermission()
    perm3 = RoleBasedPermission(["admin", "user"])

    # Use the & operator to create AND permission
    combined = perm1 & perm2 & perm3

    @strawberry.type
    class Query:
        @strawberry.field(extensions=[PermissionExtension(permissions=[combined])])
        def protected_field(self) -> str:
            return "data"

    schema = strawberry.Schema(query=Query)
    query = "{ protectedField }"

    @benchmark
    def execute():
        result = schema.execute_sync(
            query, context_value={"user": {"is_authenticated": True, "role": "admin"}}
        )
        assert result.errors is None
        return result


@pytest.mark.benchmark
def test_and_permission_early_exit(benchmark: BenchmarkFixture):
    """Benchmark AND permission with early exit (first returns False)."""

    # First permission returns False - should exit immediately
    perm1 = SyncPermissionAlwaysFalse()
    perm2 = SyncPermissionAlwaysTrue()  # This should never be evaluated
    perm3 = SyncPermissionAlwaysTrue()  # This should never be evaluated

    combined = perm1 & perm2 & perm3

    @strawberry.type
    class Query:
        @strawberry.field(
            extensions=[PermissionExtension(permissions=[combined], fail_silently=True)]
        )
        def protected_field(self) -> str | None:
            return "data"

    schema = strawberry.Schema(query=Query)
    query = "{ protectedField }"

    @benchmark
    def execute():
        result = schema.execute_sync(query, context_value={})
        # Field should return None due to fail_silently
        assert result.data == {"protectedField": None}
        return result


@pytest.mark.benchmark
def test_or_permission_all_sync(benchmark: BenchmarkFixture):
    """Benchmark OR permissions with all synchronous checks."""

    perm1 = SyncPermissionAlwaysFalse()
    perm2 = SyncPermissionAlwaysFalse()
    perm3 = SyncPermissionAlwaysTrue()  # This one succeeds

    # Use the | operator to create OR permission
    combined = perm1 | perm2 | perm3

    @strawberry.type
    class Query:
        @strawberry.field(extensions=[PermissionExtension(permissions=[combined])])
        def protected_field(self) -> str:
            return "data"

    schema = strawberry.Schema(query=Query)
    query = "{ protectedField }"

    @benchmark
    def execute():
        result = schema.execute_sync(query, context_value={})
        assert result.errors is None
        return result


@pytest.mark.benchmark
def test_or_permission_early_exit(benchmark: BenchmarkFixture):
    """Benchmark OR permission with early exit (first returns True)."""

    # First permission returns True - should exit immediately
    perm1 = SyncPermissionAlwaysTrue()
    perm2 = SyncPermissionAlwaysFalse()  # This should never be evaluated
    perm3 = SyncPermissionAlwaysFalse()  # This should never be evaluated

    combined = perm1 | perm2 | perm3

    @strawberry.type
    class Query:
        @strawberry.field(extensions=[PermissionExtension(permissions=[combined])])
        def protected_field(self) -> str:
            return "data"

    schema = strawberry.Schema(query=Query)
    query = "{ protectedField }"

    @benchmark
    def execute():
        result = schema.execute_sync(query, context_value={})
        assert result.errors is None
        return result


@pytest.mark.benchmark
def test_mixed_sync_async_permissions(benchmark: BenchmarkFixture):
    """Benchmark mixed sync/async permissions."""

    perm1 = SyncPermissionAlwaysTrue()
    perm2 = AsyncPermissionAlwaysTrue()
    perm3 = UserBasedPermission()

    combined = perm1 & perm2 & perm3

    @strawberry.type
    class Query:
        @strawberry.field(extensions=[PermissionExtension(permissions=[combined])])
        def protected_field(self) -> str:
            return "data"

    schema = strawberry.Schema(query=Query)
    query = "{ protectedField }"

    @benchmark
    def execute():
        result = asyncio.run(
            schema.execute(query, context_value={"user": {"is_authenticated": True}})
        )
        assert result.errors is None
        return result


@pytest.mark.benchmark
def test_complex_boolean_permissions(benchmark: BenchmarkFixture):
    """Benchmark complex boolean permission expressions."""

    is_authenticated = UserBasedPermission()
    is_admin = RoleBasedPermission(["admin"])
    is_moderator = RoleBasedPermission(["moderator"])
    is_owner = SyncPermissionAlwaysTrue()  # Simplified for benchmark

    # Complex boolean expression: (authenticated AND (admin OR moderator)) OR owner
    combined = (is_authenticated & (is_admin | is_moderator)) | is_owner

    @strawberry.type
    class Query:
        @strawberry.field(extensions=[PermissionExtension(permissions=[combined])])
        def protected_field(self) -> str:
            return "data"

    schema = strawberry.Schema(query=Query)
    query = "{ protectedField }"

    @benchmark
    def execute():
        result = schema.execute_sync(
            query,
            context_value={"user": {"is_authenticated": True, "role": "moderator"}},
        )
        assert result.errors is None
        return result


@pytest.mark.benchmark
def test_permission_with_context(benchmark: BenchmarkFixture):
    """Benchmark permissions that return context with False."""

    @strawberry.type
    class Query:
        @strawberry.field(
            extensions=[
                PermissionExtension(
                    permissions=[SyncPermissionWithContext()], fail_silently=True
                )
            ]
        )
        def protected_field(self) -> str | None:
            return "data"

    schema = strawberry.Schema(query=Query)
    query = "{ protectedField }"

    @benchmark
    def execute():
        result = schema.execute_sync(query, context_value={})
        # Should return None due to fail_silently
        assert result.data == {"protectedField": None}
        return result


@pytest.mark.benchmark
def test_multiple_fields_with_permissions(benchmark: BenchmarkFixture):
    """Benchmark schema with multiple fields having different permissions."""

    @strawberry.type
    class Query:
        @strawberry.field(
            extensions=[PermissionExtension(permissions=[SyncPermissionAlwaysTrue()])]
        )
        def field1(self) -> str:
            return "data1"

        @strawberry.field(
            extensions=[PermissionExtension(permissions=[UserBasedPermission()])]
        )
        def field2(self) -> str:
            return "data2"

        @strawberry.field(
            extensions=[
                PermissionExtension(
                    permissions=[RoleBasedPermission(["admin", "moderator"])]
                )
            ]
        )
        def field3(self) -> str:
            return "data3"

        @strawberry.field(
            extensions=[
                PermissionExtension(
                    permissions=[SyncPermissionAlwaysTrue() & UserBasedPermission()]
                )
            ]
        )
        def field4(self) -> str:
            return "data4"

        @strawberry.field(
            extensions=[
                PermissionExtension(
                    permissions=[
                        RoleBasedPermission(["admin"])
                        | RoleBasedPermission(["moderator"])
                    ]
                )
            ]
        )
        def field5(self) -> str:
            return "data5"

    schema = strawberry.Schema(query=Query)
    query = "{ field1 field2 field3 field4 field5 }"

    @benchmark
    def execute():
        result = schema.execute_sync(
            query, context_value={"user": {"is_authenticated": True, "role": "admin"}}
        )
        assert result.errors is None
        assert result.data == {
            "field1": "data1",
            "field2": "data2",
            "field3": "data3",
            "field4": "data4",
            "field5": "data5",
        }
        return result
