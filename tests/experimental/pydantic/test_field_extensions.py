"""Test that field extensions work properly with pydantic types."""

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

import strawberry
from strawberry.experimental.pydantic import type as pyd_type
from strawberry.extensions.field_extension import FieldExtension


class TrackingExtension(FieldExtension):
    """Extension that tracks field resolution calls."""

    def __init__(self, call_log: list[str]):
        self.call_log = call_log

    def resolve(
        self,
        next_: Callable[..., Any],
        source: Any,
        info: strawberry.Info,
        **kwargs: Any,
    ) -> Any:
        self.call_log.append(info.field_name)
        return next_(source, info, **kwargs)


class UpperCaseExtension(FieldExtension):
    """Extension that uppercases string results."""

    def resolve(
        self,
        next_: Callable[..., Any],
        source: Any,
        info: strawberry.Info,
        **kwargs: Any,
    ) -> Any:
        result = next_(source, info, **kwargs)
        return str(result).upper()


class MaskingExtension(FieldExtension):
    """Extension that masks field value based on permission."""

    def __init__(self, required_role: str):
        self.required_role = required_role

    def resolve(
        self,
        next_: Callable[..., Any],
        source: Any,
        info: strawberry.Info,
        **kwargs: Any,
    ) -> Any:
        # Check if context has user with required role
        user = info.context.get("user")
        if not user or user.get("role") != self.required_role:
            return None  # Mask field
        return next_(source, info, **kwargs)


def test_extension_called_on_pydantic_field():
    """Test that a simple extension is called when resolving a pydantic field."""
    call_log = []

    class UserModel(BaseModel):
        id: int
        name: str

    @pyd_type(model=UserModel)
    class User:
        id: strawberry.auto
        name: str = strawberry.field(extensions=[TrackingExtension(call_log)])

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User.from_pydantic(UserModel(id=1, name="Alice"))

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("{ user { name } }")

    assert result.errors is None
    assert result.data == {"user": {"name": "Alice"}}
    assert "name" in call_log, "Extension should have been called for 'name' field"


def test_extension_modifies_pydantic_field_result():
    """Test that an extension can modify the result of a pydantic field."""

    class UserModel(BaseModel):
        id: int
        name: str

    @pyd_type(model=UserModel)
    class User:
        id: strawberry.auto
        name: str = strawberry.field(extensions=[UpperCaseExtension()])

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User.from_pydantic(UserModel(id=1, name="alice"))

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("{ user { name } }")

    assert result.errors is None
    assert result.data == {"user": {"name": "ALICE"}}


def test_multiple_extensions_chain_on_pydantic_field():
    """Test that multiple extensions are chained correctly on pydantic fields."""
    call_log = []

    class DoubleExtension(FieldExtension):
        def resolve(
            self,
            next_: Callable[..., Any],
            source: Any,
            info: strawberry.Info,
            **kwargs: Any,
        ) -> Any:
            result = next_(source, info, **kwargs)
            return f"{result}{result}"

    class UserModel(BaseModel):
        name: str

    @pyd_type(model=UserModel)
    class User:
        name: str = strawberry.field(
            extensions=[
                TrackingExtension(call_log),
                UpperCaseExtension(),
                DoubleExtension(),
            ]
        )

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User.from_pydantic(UserModel(name="x"))

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("{ user { name } }")

    assert result.errors is None
    # Extensions execute in order: track -> uppercase -> double
    # "x" -> "X" -> "XX"
    assert result.data == {"user": {"name": "XX"}}
    assert "name" in call_log


def test_extension_with_context_on_pydantic_field():
    """Test that extensions on pydantic fields can access context."""

    class RequireAuthExtension(FieldExtension):
        """Extension that masks field if user is not authenticated."""

        def resolve(
            self,
            next_: Callable[..., Any],
            source: Any,
            info: strawberry.Info,
            **kwargs: Any,
        ) -> Any:
            # Check if context has authenticated user
            is_authenticated = info.context.get("is_authenticated", False)
            if not is_authenticated:
                return None  # Mask field
            return next_(source, info, **kwargs)

    class UserModel(BaseModel):
        id: int
        name: str
        email: str

    @pyd_type(model=UserModel)
    class User:
        id: strawberry.auto
        name: strawberry.auto
        email: str | None = strawberry.field(extensions=[RequireAuthExtension()])

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User.from_pydantic(
                UserModel(id=1, name="Alice", email="alice@example.com")
            )

    schema = strawberry.Schema(query=Query)

    # Test with authenticated user - can see email
    result = schema.execute_sync(
        "{ user { id name email } }", context_value={"is_authenticated": True}
    )
    assert result.errors is None
    assert result.data == {
        "user": {"id": 1, "name": "Alice", "email": "alice@example.com"}
    }

    # Test with unauthenticated user - email is masked
    result = schema.execute_sync(
        "{ user { id name email } }", context_value={"is_authenticated": False}
    )
    assert result.errors is None
    assert result.data == {"user": {"id": 1, "name": "Alice", "email": None}}


def test_extension_on_field_without_strawberry_auto():
    """Test extensions work on fields that are not auto fields."""

    class ProductModel(BaseModel):
        id: int
        name: str
        description: str

    @pyd_type(model=ProductModel)
    class Product:
        id: strawberry.auto
        name: str = strawberry.field(extensions=[UpperCaseExtension()])
        description: str = strawberry.field(extensions=[UpperCaseExtension()])

    @strawberry.type
    class Query:
        @strawberry.field
        def product(self) -> Product:
            return Product.from_pydantic(
                ProductModel(id=1, name="widget", description="a useful tool")
            )

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("{ product { name description } }")

    assert result.errors is None
    assert result.data == {
        "product": {"name": "WIDGET", "description": "A USEFUL TOOL"}
    }


def test_extension_with_custom_resolver_on_pydantic_field():
    """Test that extensions work when field also has a custom resolver."""

    class UserModel(BaseModel):
        first_name: str
        last_name: str

    @pyd_type(model=UserModel)
    class User:
        first_name: strawberry.auto
        last_name: strawberry.auto

        @strawberry.field(extensions=[UpperCaseExtension()])
        def full_name(self) -> str:
            return f"{self.first_name} {self.last_name}"

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User.from_pydantic(UserModel(first_name="alice", last_name="smith"))

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("{ user { fullName } }")

    assert result.errors is None
    assert result.data == {"user": {"fullName": "ALICE SMITH"}}


async def test_async_extension_on_pydantic_field():
    """Test that async extensions work on pydantic fields."""

    class AsyncUpperCaseExtension(FieldExtension):
        async def resolve_async(
            self,
            next_: Callable[..., Any],
            source: Any,
            info: strawberry.Info,
            **kwargs: Any,
        ) -> Any:
            result = await next_(source, info, **kwargs)
            return str(result).upper()

    class UserModel(BaseModel):
        name: str

    @pyd_type(model=UserModel)
    class User:
        name: str = strawberry.field(extensions=[AsyncUpperCaseExtension()])

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User.from_pydantic(UserModel(name="alice"))

    schema = strawberry.Schema(query=Query)
    result = await schema.execute("{ user { name } }")

    assert result.errors is None
    assert result.data == {"user": {"name": "ALICE"}}
