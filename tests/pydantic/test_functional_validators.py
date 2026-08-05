"""Tests for Pydantic v2 functional validators with first-class integration."""

from typing import Annotated, Any

import pydantic
from pydantic import AfterValidator, BeforeValidator

import strawberry


def test_after_validator_runs_on_input():
    """Test that AfterValidator runs during GraphQL input processing."""

    def validate_email(v: str) -> str:
        if "@" not in v:
            raise ValueError("Invalid email format")
        return v.lower()

    Email = Annotated[str, AfterValidator(validate_email)]

    @strawberry.pydantic.input
    class UserInput(pydantic.BaseModel):
        email: Email

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        email: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_user(self, input: UserInput) -> User:
            return User(email=input.email)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test valid email - should be lowercased
    result = schema.execute_sync(
        """
        mutation {
            createUser(input: { email: "TEST@EXAMPLE.COM" }) {
                email
            }
        }
        """
    )

    assert not result.errors
    assert result.data["createUser"]["email"] == "test@example.com"

    # Test invalid email
    result = schema.execute_sync(
        """
        mutation {
            createUser(input: { email: "invalid" }) {
                email
            }
        }
        """
    )

    assert result.errors is not None
    assert len(result.errors) == 1
    assert "Invalid email format" in result.errors[0].message


def test_before_validator_transforms_input():
    """Test that BeforeValidator transforms data before type validation."""

    def parse_tags(v: Any) -> list[str]:
        if isinstance(v, str):
            return [tag.strip() for tag in v.split(",")]
        return v

    TagList = Annotated[list[str], BeforeValidator(parse_tags)]

    @strawberry.pydantic.input
    class PostInput(pydantic.BaseModel):
        title: str
        tags: TagList

    @strawberry.pydantic.type
    class Post(pydantic.BaseModel):
        title: str
        tags: list[str]

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_post(self, input: PostInput) -> Post:
            return Post(title=input.title, tags=input.tags)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test with list input
    result = schema.execute_sync(
        """
        mutation {
            createPost(input: { title: "Hello", tags: ["python", "graphql"] }) {
                title
                tags
            }
        }
        """
    )

    assert not result.errors
    assert result.data["createPost"]["tags"] == ["python", "graphql"]


def test_multiple_validators_chain():
    """Test that multiple validators chain correctly."""

    def strip_whitespace(v: str) -> str:
        return v.strip()

    def to_lowercase(v: str) -> str:
        return v.lower()

    def check_not_empty(v: str) -> str:
        if not v:
            raise ValueError("Cannot be empty")
        return v

    CleanString = Annotated[
        str,
        BeforeValidator(strip_whitespace),
        BeforeValidator(to_lowercase),
        AfterValidator(check_not_empty),
    ]

    @strawberry.pydantic.input
    class UsernameInput(pydantic.BaseModel):
        username: CleanString

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        username: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_user(self, input: UsernameInput) -> User:
            return User(username=input.username)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test transformation chain
    result = schema.execute_sync(
        """
        mutation {
            createUser(input: { username: "  ALICE  " }) {
                username
            }
        }
        """
    )

    assert not result.errors
    assert result.data["createUser"]["username"] == "alice"

    # Test empty string after strip
    result = schema.execute_sync(
        """
        mutation {
            createUser(input: { username: "   " }) {
                username
            }
        }
        """
    )

    assert result.errors is not None
    assert "Cannot be empty" in result.errors[0].message


def test_validator_with_field_constraints():
    """Test validators combined with Field constraints."""

    def normalize_phone(v: str) -> str:
        # Remove non-digits
        return "".join(c for c in v if c.isdigit())

    Phone = Annotated[
        str,
        BeforeValidator(normalize_phone),
        pydantic.Field(min_length=10, max_length=11),
    ]

    @strawberry.pydantic.input
    class ContactInput(pydantic.BaseModel):
        phone: Phone

    @strawberry.pydantic.type
    class Contact(pydantic.BaseModel):
        phone: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_contact(self, input: ContactInput) -> Contact:
            return Contact(phone=input.phone)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test with formatted phone number
    result = schema.execute_sync(
        """
        mutation {
            createContact(input: { phone: "(555) 123-4567" }) {
                phone
            }
        }
        """
    )

    assert not result.errors
    assert result.data["createContact"]["phone"] == "5551234567"

    # Test with too short phone
    result = schema.execute_sync(
        """
        mutation {
            createContact(input: { phone: "123" }) {
                phone
            }
        }
        """
    )

    assert result.errors is not None
    assert "too_short" in result.errors[0].message


def test_reusable_annotated_types_across_models():
    """Test that Annotated types can be reused across multiple models."""

    def validate_positive(v: int) -> int:
        if v <= 0:
            raise ValueError("Must be positive")
        return v

    PositiveInt = Annotated[int, AfterValidator(validate_positive)]

    @strawberry.pydantic.input
    class OrderInput(pydantic.BaseModel):
        quantity: PositiveInt
        price_cents: PositiveInt

    @strawberry.pydantic.input
    class InventoryInput(pydantic.BaseModel):
        stock_count: PositiveInt

    @strawberry.pydantic.type
    class Result(pydantic.BaseModel):
        success: bool

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_order(self, input: OrderInput) -> Result:
            return Result(success=True)

        @strawberry.mutation
        def update_inventory(self, input: InventoryInput) -> Result:
            return Result(success=True)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test OrderInput validation
    result = schema.execute_sync(
        """
        mutation {
            createOrder(input: { quantity: 0, priceCents: 100 }) {
                success
            }
        }
        """
    )

    assert result.errors is not None
    assert "Must be positive" in result.errors[0].message

    # Test InventoryInput validation
    result = schema.execute_sync(
        """
        mutation {
            updateInventory(input: { stockCount: -5 }) {
                success
            }
        }
        """
    )

    assert result.errors is not None
    assert "Must be positive" in result.errors[0].message

    # Test valid inputs
    result = schema.execute_sync(
        """
        mutation {
            createOrder(input: { quantity: 5, priceCents: 1000 }) {
                success
            }
        }
        """
    )

    assert not result.errors
    assert result.data["createOrder"]["success"] is True
