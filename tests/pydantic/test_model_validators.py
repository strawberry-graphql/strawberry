"""Tests for Pydantic v2 @model_validator with first-class integration."""

from datetime import date
from typing import Any

import pydantic
from pydantic import model_validator

import strawberry


def test_model_validator_after_mode():
    """Test @model_validator with mode='after' for cross-field validation."""

    @strawberry.pydantic.input
    class DateRangeInput(pydantic.BaseModel):
        start_date: date
        end_date: date

        @model_validator(mode="after")
        def check_dates(self) -> "DateRangeInput":
            if self.start_date > self.end_date:
                raise ValueError("start_date must be before end_date")
            return self

    @strawberry.pydantic.type
    class DateRange(pydantic.BaseModel):
        start_date: date
        end_date: date

    @strawberry.type
    class Query:
        @strawberry.field
        def validate_range(self, input: DateRangeInput) -> DateRange:
            return DateRange(start_date=input.start_date, end_date=input.end_date)

    schema = strawberry.Schema(query=Query)

    # Test valid date range
    result = schema.execute_sync(
        """
        query {
            validateRange(input: { startDate: "2024-01-01", endDate: "2024-12-31" }) {
                startDate
                endDate
            }
        }
        """
    )

    assert not result.errors
    assert result.data["validateRange"]["startDate"] == "2024-01-01"
    assert result.data["validateRange"]["endDate"] == "2024-12-31"

    # Test invalid date range (start after end)
    result = schema.execute_sync(
        """
        query {
            validateRange(input: { startDate: "2024-12-31", endDate: "2024-01-01" }) {
                startDate
                endDate
            }
        }
        """
    )

    assert result.errors is not None
    assert len(result.errors) == 1
    assert "start_date must be before end_date" in result.errors[0].message


def test_model_validator_before_mode():
    """Test @model_validator with mode='before' for input transformation."""

    @strawberry.pydantic.input
    class UserInput(pydantic.BaseModel):
        email: str
        username: str

        @model_validator(mode="before")
        @classmethod
        def extract_username(cls, data: Any) -> Any:
            if isinstance(data, dict) and "email" in data and not data.get("username"):
                # Auto-generate username from email
                data["username"] = data["email"].split("@")[0]
            return data

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        email: str
        username: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_user(self, input: UserInput) -> User:
            return User(email=input.email, username=input.username)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test with explicit username
    result = schema.execute_sync(
        """
        mutation {
            createUser(input: { email: "alice@example.com", username: "alice_custom" }) {
                email
                username
            }
        }
        """
    )

    assert not result.errors
    assert result.data["createUser"]["username"] == "alice_custom"

    # Test with auto-generated username - note: this won't work with GraphQL
    # since GraphQL requires the field to be provided. This is more for
    # programmatic usage where the validator can add missing fields.


def test_model_validator_password_confirmation():
    """Test @model_validator for password confirmation pattern."""

    @strawberry.pydantic.input
    class RegistrationInput(pydantic.BaseModel):
        email: str
        password: str
        password_confirm: str

        @model_validator(mode="after")
        def check_passwords_match(self) -> "RegistrationInput":
            if self.password != self.password_confirm:
                raise ValueError("Passwords do not match")
            return self

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        email: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def register(self, input: RegistrationInput) -> User:
            return User(email=input.email)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test matching passwords
    result = schema.execute_sync(
        """
        mutation {
            register(input: {
                email: "test@example.com"
                password: "secret123"
                passwordConfirm: "secret123"
            }) {
                email
            }
        }
        """
    )

    assert not result.errors
    assert result.data["register"]["email"] == "test@example.com"

    # Test mismatched passwords
    result = schema.execute_sync(
        """
        mutation {
            register(input: {
                email: "test@example.com"
                password: "secret123"
                passwordConfirm: "different456"
            }) {
                email
            }
        }
        """
    )

    assert result.errors is not None
    assert "Passwords do not match" in result.errors[0].message


def test_model_validator_conditional_required_fields():
    """Test @model_validator for conditional field requirements."""

    @strawberry.pydantic.input
    class PaymentInput(pydantic.BaseModel):
        payment_method: str
        card_number: str | None = None
        bank_account: str | None = None

        @model_validator(mode="after")
        def check_payment_details(self) -> "PaymentInput":
            if self.payment_method == "card" and not self.card_number:
                raise ValueError("Card number required for card payments")
            if self.payment_method == "bank" and not self.bank_account:
                raise ValueError("Bank account required for bank payments")
            return self

    @strawberry.pydantic.type
    class PaymentResult(pydantic.BaseModel):
        success: bool
        method: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def process_payment(self, input: PaymentInput) -> PaymentResult:
            return PaymentResult(success=True, method=input.payment_method)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test valid card payment
    result = schema.execute_sync(
        """
        mutation {
            processPayment(input: {
                paymentMethod: "card"
                cardNumber: "4111111111111111"
            }) {
                success
                method
            }
        }
        """
    )

    assert not result.errors
    assert result.data["processPayment"]["success"] is True

    # Test card payment without card number
    result = schema.execute_sync(
        """
        mutation {
            processPayment(input: {
                paymentMethod: "card"
            }) {
                success
                method
            }
        }
        """
    )

    assert result.errors is not None
    assert "Card number required" in result.errors[0].message

    # Test bank payment without bank account
    result = schema.execute_sync(
        """
        mutation {
            processPayment(input: {
                paymentMethod: "bank"
            }) {
                success
                method
            }
        }
        """
    )

    assert result.errors is not None
    assert "Bank account required" in result.errors[0].message


def test_model_validator_nested_inputs():
    """Test @model_validator with nested input types."""

    @strawberry.pydantic.input
    class AddressInput(pydantic.BaseModel):
        street: str
        city: str
        country: str

    @strawberry.pydantic.input
    class OrderInput(pydantic.BaseModel):
        billing_address: AddressInput
        shipping_address: AddressInput | None = None
        same_as_billing: bool = False

        @model_validator(mode="after")
        def check_shipping(self) -> "OrderInput":
            if not self.same_as_billing and not self.shipping_address:
                raise ValueError(
                    "Shipping address required unless same_as_billing is true"
                )
            return self

    @strawberry.pydantic.type
    class Order(pydantic.BaseModel):
        id: int

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_order(self, input: OrderInput) -> Order:
            return Order(id=1)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test with same_as_billing=true (no shipping needed)
    result = schema.execute_sync(
        """
        mutation {
            createOrder(input: {
                billingAddress: { street: "123 Main", city: "NYC", country: "USA" }
                sameAsBilling: true
            }) {
                id
            }
        }
        """
    )

    assert not result.errors
    assert result.data["createOrder"]["id"] == 1

    # Test with explicit shipping address
    result = schema.execute_sync(
        """
        mutation {
            createOrder(input: {
                billingAddress: { street: "123 Main", city: "NYC", country: "USA" }
                shippingAddress: { street: "456 Oak", city: "LA", country: "USA" }
                sameAsBilling: false
            }) {
                id
            }
        }
        """
    )

    assert not result.errors

    # Test missing shipping when required
    result = schema.execute_sync(
        """
        mutation {
            createOrder(input: {
                billingAddress: { street: "123 Main", city: "NYC", country: "USA" }
                sameAsBilling: false
            }) {
                id
            }
        }
        """
    )

    assert result.errors is not None
    assert "Shipping address required" in result.errors[0].message


def test_model_validator_multiple_errors():
    """Test @model_validator that raises multiple validation errors."""

    @strawberry.pydantic.input
    class ProfileInput(pydantic.BaseModel):
        username: str
        age: int
        website: str | None = None

        @model_validator(mode="after")
        def validate_profile(self) -> "ProfileInput":
            errors = []

            if len(self.username) < 3:
                errors.append("Username must be at least 3 characters")

            if self.age < 13:
                errors.append("Must be at least 13 years old")

            if self.website and not self.website.startswith(("http://", "https://")):
                errors.append("Website must start with http:// or https://")

            if errors:
                raise ValueError("; ".join(errors))

            return self

    @strawberry.pydantic.type
    class Profile(pydantic.BaseModel):
        username: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_profile(self, input: ProfileInput) -> Profile:
            return Profile(username=input.username)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test with multiple validation errors
    result = schema.execute_sync(
        """
        mutation {
            createProfile(input: {
                username: "ab"
                age: 10
                website: "invalid"
            }) {
                username
            }
        }
        """
    )

    assert result.errors is not None
    error_message = result.errors[0].message
    assert "Username must be at least 3 characters" in error_message
    assert "Must be at least 13 years old" in error_message
    assert "Website must start with" in error_message
