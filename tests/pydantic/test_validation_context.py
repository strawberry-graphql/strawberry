"""Tests for Pydantic validation context with Strawberry Info."""

from typing import Any

import pydantic
from pydantic import ValidationInfo, field_validator, model_validator

import strawberry
from strawberry.types.info import Info


def test_validation_context_passed_to_field_validator():
    """Test that Strawberry Info is passed to Pydantic field validators."""

    received_context: dict[str, Any] = {}

    @strawberry.pydantic.input
    class UserInput(pydantic.BaseModel):
        name: str

        @field_validator("name")
        @classmethod
        def capture_context(cls, v: str, info: ValidationInfo) -> str:
            # Capture the context for testing
            if info.context:
                received_context.update(info.context)
            return v

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_user(self, input: UserInput) -> User:
            return User(name=input.name)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    result = schema.execute_sync(
        """
        mutation {
            createUser(input: { name: "Alice" }) {
                name
            }
        }
        """
    )

    assert not result.errors
    assert result.data["createUser"]["name"] == "Alice"

    # Verify that context was passed (should contain 'info')
    assert "info" in received_context
    assert isinstance(received_context["info"], Info)


def test_validation_context_passed_to_model_validator():
    """Test that Strawberry Info is passed to Pydantic model validators."""

    received_context: dict[str, Any] = {}

    @strawberry.pydantic.input
    class OrderInput(pydantic.BaseModel):
        quantity: int
        price: int

        @model_validator(mode="after")
        def capture_context(self, info: ValidationInfo) -> "OrderInput":
            if info.context:
                received_context.update(info.context)
            return self

    @strawberry.pydantic.type
    class Order(pydantic.BaseModel):
        quantity: int
        price: int

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_order(self, input: OrderInput) -> Order:
            return Order(quantity=input.quantity, price=input.price)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    result = schema.execute_sync(
        """
        mutation {
            createOrder(input: { quantity: 5, price: 100 }) {
                quantity
                price
            }
        }
        """
    )

    assert not result.errors
    assert "info" in received_context
    assert isinstance(received_context["info"], Info)


def test_validation_context_with_custom_context():
    """Test that user's custom context is also passed to validators."""

    received_context: dict[str, Any] = {}

    @strawberry.pydantic.input
    class PostInput(pydantic.BaseModel):
        title: str

        @field_validator("title")
        @classmethod
        def check_context(cls, v: str, info: ValidationInfo) -> str:
            if info.context:
                received_context.update(info.context)
            return v

    @strawberry.pydantic.type
    class Post(pydantic.BaseModel):
        title: str

    class CustomContext:
        def __init__(self, user_id: int):
            self.user_id = user_id

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_post(self, input: PostInput) -> Post:
            return Post(title=input.title)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Execute with custom context
    result = schema.execute_sync(
        """
        mutation {
            createPost(input: { title: "Hello World" }) {
                title
            }
        }
        """,
        context_value=CustomContext(user_id=42),
    )

    assert not result.errors

    # Verify both info and strawberry_context are available
    assert "info" in received_context
    assert "strawberry_context" in received_context
    assert received_context["strawberry_context"].user_id == 42


def test_validation_context_for_permission_based_validation():
    """Test using validation context for permission-based validation."""

    class UserContext:
        def __init__(self, role: str):
            self.role = role

    @strawberry.pydantic.input
    class AdminActionInput(pydantic.BaseModel):
        action: str

        @field_validator("action")
        @classmethod
        def check_admin_permission(cls, v: str, info: ValidationInfo) -> str:
            if info.context:
                strawberry_ctx = info.context.get("strawberry_context")
                if (
                    strawberry_ctx
                    and hasattr(strawberry_ctx, "role")
                    and strawberry_ctx.role != "admin"
                ):
                    raise ValueError("Only admins can perform this action")
            return v

    @strawberry.pydantic.type
    class ActionResult(pydantic.BaseModel):
        success: bool
        action: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def perform_admin_action(self, input: AdminActionInput) -> ActionResult:
            return ActionResult(success=True, action=input.action)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test with admin user - should succeed
    result = schema.execute_sync(
        """
        mutation {
            performAdminAction(input: { action: "delete_all" }) {
                success
                action
            }
        }
        """,
        context_value=UserContext(role="admin"),
    )

    assert not result.errors
    assert result.data["performAdminAction"]["success"] is True

    # Test with non-admin user - should fail
    result = schema.execute_sync(
        """
        mutation {
            performAdminAction(input: { action: "delete_all" }) {
                success
                action
            }
        }
        """,
        context_value=UserContext(role="user"),
    )

    assert result.errors is not None
    assert "Only admins can perform this action" in result.errors[0].message


def test_validation_context_with_nested_inputs():
    """Test that validation context is passed to nested input validators."""

    nested_context_received = {"outer": False, "inner": False}

    @strawberry.pydantic.input
    class AddressInput(pydantic.BaseModel):
        city: str

        @field_validator("city")
        @classmethod
        def check_inner(cls, v: str, info: ValidationInfo) -> str:
            if info.context and "info" in info.context:
                nested_context_received["inner"] = True
            return v

    @strawberry.pydantic.input
    class PersonInput(pydantic.BaseModel):
        name: str
        address: AddressInput

        @field_validator("name")
        @classmethod
        def check_outer(cls, v: str, info: ValidationInfo) -> str:
            if info.context and "info" in info.context:
                nested_context_received["outer"] = True
            return v

    @strawberry.pydantic.type
    class Person(pydantic.BaseModel):
        name: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_person(self, input: PersonInput) -> Person:
            return Person(name=input.name)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    result = schema.execute_sync(
        """
        mutation {
            createPerson(input: {
                name: "Alice"
                address: { city: "NYC" }
            }) {
                name
            }
        }
        """
    )

    assert not result.errors
    # Both outer and inner validators should receive context
    assert nested_context_received["outer"] is True
    assert nested_context_received["inner"] is True


def test_validation_context_in_query_arguments():
    """Test that validation context works for query arguments too."""

    context_received = {"received": False}

    @strawberry.pydantic.input
    class FilterInput(pydantic.BaseModel):
        search: str

        @field_validator("search")
        @classmethod
        def check_context(cls, v: str, info: ValidationInfo) -> str:
            if info.context and "info" in info.context:
                context_received["received"] = True
            return v

    @strawberry.type
    class Query:
        @strawberry.field
        def search(self, filter: FilterInput) -> str:
            return f"Searching for: {filter.search}"

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        """
        query {
            search(filter: { search: "test" })
        }
        """
    )

    assert not result.errors
    assert context_received["received"] is True
