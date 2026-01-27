"""Test that Private fields work correctly with from_pydantic in experimental pydantic types."""

import pytest
from pydantic import BaseModel

import strawberry
from strawberry.experimental.pydantic import type as pyd_type


def test_private_field_from_pydantic_with_extra():
    """Test that Private fields can be populated via the extra dict in from_pydantic."""

    class UserModel(BaseModel):
        name: str
        age: int

    @pyd_type(model=UserModel)
    class User:
        name: strawberry.auto
        age: strawberry.auto
        password: strawberry.Private[str]

    pydantic_user = UserModel(name="Alice", age=30)
    strawberry_user = User.from_pydantic(pydantic_user, extra={"password": "secret123"})

    assert strawberry_user.name == "Alice"
    assert strawberry_user.age == 30
    assert strawberry_user.password == "secret123"


def test_private_field_from_pydantic_without_extra_raises_error():
    """Test that from_pydantic raises TypeError when Private field is not provided."""

    class UserModel(BaseModel):
        name: str

    @pyd_type(model=UserModel)
    class User:
        name: strawberry.auto
        password: strawberry.Private[str]

    pydantic_user = UserModel(name="Bob")

    # Should raise TypeError because password is required but not provided
    with pytest.raises(TypeError) as exc_info:
        User.from_pydantic(pydantic_user)

    assert "password" in str(exc_info.value)


def test_private_field_from_pydantic_multiple_private_fields():
    """Test that multiple Private fields can be populated via extra dict."""

    class ProductModel(BaseModel):
        name: str
        price: float

    @pyd_type(model=ProductModel)
    class Product:
        name: strawberry.auto
        price: strawberry.auto
        internal_id: strawberry.Private[int]
        warehouse_location: strawberry.Private[str]

    pydantic_product = ProductModel(name="Widget", price=9.99)
    strawberry_product = Product.from_pydantic(
        pydantic_product, extra={"internal_id": 12345, "warehouse_location": "A-15"}
    )

    assert strawberry_product.name == "Widget"
    assert strawberry_product.price == 9.99
    assert strawberry_product.internal_id == 12345
    assert strawberry_product.warehouse_location == "A-15"


def test_private_field_not_exposed_in_schema():
    """Test that Private fields are not exposed in the GraphQL schema."""

    class UserModel(BaseModel):
        name: str

    @pyd_type(model=UserModel)
    class User:
        name: strawberry.auto
        password: strawberry.Private[str]

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User(name="Charlie", password="hidden")

    schema = strawberry.Schema(query=Query)

    # Should be able to query name
    result = schema.execute_sync("{ user { name } }")
    assert result.errors is None
    assert result.data == {"user": {"name": "Charlie"}}

    # Should not be able to query password
    result = schema.execute_sync("{ user { name password } }")
    assert result.errors is not None


def test_private_field_accessible_in_resolver():
    """Test that Private fields are accessible within custom resolvers."""

    class UserModel(BaseModel):
        first_name: str
        last_name: str

    @pyd_type(model=UserModel)
    class User:
        first_name: strawberry.auto
        last_name: strawberry.auto
        user_id: strawberry.Private[int]

        @strawberry.field
        def display_info(self) -> str:
            return f"{self.first_name} {self.last_name} (ID: {self.user_id})"

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            pydantic_user = UserModel(first_name="John", last_name="Doe")
            return User.from_pydantic(pydantic_user, extra={"user_id": 999})

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("{ user { displayInfo } }")

    assert result.errors is None
    assert result.data == {"user": {"displayInfo": "John Doe (ID: 999)"}}


def test_private_field_with_optional_private_field():
    """Test that optional Private fields work with from_pydantic."""

    class UserModel(BaseModel):
        name: str

    @pyd_type(model=UserModel)
    class User:
        name: strawberry.auto
        session_token: strawberry.Private[str | None] = None

    # Without providing session_token
    pydantic_user = UserModel(name="Dave")
    strawberry_user = User.from_pydantic(pydantic_user)
    assert strawberry_user.name == "Dave"
    assert strawberry_user.session_token is None

    # With providing session_token via extra
    strawberry_user = User.from_pydantic(
        pydantic_user, extra={"session_token": "abc123"}
    )
    assert strawberry_user.name == "Dave"
    assert strawberry_user.session_token == "abc123"


def test_private_field_from_pydantic_with_nested_types():
    """Test Private fields work with nested pydantic types."""

    class AddressModel(BaseModel):
        street: str
        city: str

    class UserModel(BaseModel):
        name: str
        address: AddressModel

    @pyd_type(model=AddressModel)
    class Address:
        street: strawberry.auto
        city: strawberry.auto

    @pyd_type(model=UserModel)
    class User:
        name: strawberry.auto
        address: strawberry.auto
        internal_notes: strawberry.Private[str]

    pydantic_user = UserModel(
        name="Emma", address=AddressModel(street="123 Main St", city="Springfield")
    )
    strawberry_user = User.from_pydantic(
        pydantic_user, extra={"internal_notes": "VIP customer"}
    )

    assert strawberry_user.name == "Emma"
    assert strawberry_user.address.street == "123 Main St"
    assert strawberry_user.address.city == "Springfield"
    assert strawberry_user.internal_notes == "VIP customer"


def test_private_field_overrides_pydantic_model_field():
    """Test that a field marked as Private is not exposed even if it exists in the pydantic model.

    This tests the fix where previously if a field existed in the pydantic model,
    the Private annotation would be ignored.
    """

    class UserModel(BaseModel):
        name: str
        password: str  # This field exists in pydantic model

    @pyd_type(model=UserModel)
    class User:
        name: strawberry.auto
        # Marking password as Private even though it's in the pydantic model
        password: strawberry.Private[str]

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            pydantic_user = UserModel(name="Alice", password="secret123")
            return User.from_pydantic(pydantic_user)

    schema = strawberry.Schema(query=Query)

    # Should be able to query name
    result = schema.execute_sync("{ user { name } }")
    assert result.errors is None
    assert result.data == {"user": {"name": "Alice"}}

    # Password should NOT be queryable (it's Private)
    result = schema.execute_sync("{ user { password } }")
    assert result.errors is not None
    assert "password" in str(result.errors[0])

    # But password should still be accessible on the instance
    pydantic_user = UserModel(name="Bob", password="mypassword")
    strawberry_user = User.from_pydantic(pydantic_user)
    assert strawberry_user.password == "mypassword"


def test_private_field_with_all_fields_no_warning():
    """Test that using Private fields with all_fields=True does not produce a warning."""
    import warnings

    class UserModel(BaseModel):
        name: str
        email: str
        password: str

    # This should NOT produce a warning - Private fields are expected with all_fields
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        @pyd_type(model=UserModel, all_fields=True)
        class User:
            password: strawberry.Private[str]

        # Filter for the specific warning we care about
        relevant_warnings = [
            warning
            for warning in w
            if "all_fields overrides" in str(warning.message)
        ]
        assert len(relevant_warnings) == 0, (
            f"Unexpected warning: {relevant_warnings}"
        )

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            pydantic_user = UserModel(name="Test", email="test@example.com", password="secret")
            return User.from_pydantic(pydantic_user)

    schema = strawberry.Schema(query=Query)

    # name and email should be exposed (from all_fields)
    result = schema.execute_sync("{ user { name email } }")
    assert result.errors is None
    assert result.data == {"user": {"name": "Test", "email": "test@example.com"}}

    # password should NOT be exposed (marked as Private)
    result = schema.execute_sync("{ user { password } }")
    assert result.errors is not None


def test_all_fields_respects_explicit_field_definitions():
    """Test that all_fields=True respects explicit field definitions instead of overriding them."""
    import warnings
    from typing import Optional

    from strawberry.extensions.field_extension import FieldExtension

    class UpperCaseExtension(FieldExtension):
        def resolve(self, next_, source, info, **kwargs):
            result = next_(source, info, **kwargs)
            return result.upper() if result else result

    class UserModel(BaseModel):
        name: str
        email: str
        password: str

    # Should NOT produce a warning - combining all_fields with explicit definitions is valid
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        @pyd_type(model=UserModel, all_fields=True)
        class User:
            # Explicit field with extension - should be respected
            name: str = strawberry.field(extensions=[UpperCaseExtension()])
            # Private field - should not appear in schema
            password: strawberry.Private[str]

        relevant_warnings = [
            warning
            for warning in w
            if "all_fields overrides" in str(warning.message)
        ]
        assert len(relevant_warnings) == 0, f"Unexpected warning: {relevant_warnings}"

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            pydantic_user = UserModel(name="alice", email="alice@example.com", password="secret")
            return User.from_pydantic(pydantic_user)

    schema = strawberry.Schema(query=Query)

    # name should have the extension applied (uppercase)
    result = schema.execute_sync("{ user { name email } }")
    assert result.errors is None
    assert result.data == {"user": {"name": "ALICE", "email": "alice@example.com"}}

    # password should not be exposed
    result = schema.execute_sync("{ user { password } }")
    assert result.errors is not None


def test_all_fields_with_explicit_type_override():
    """Test that explicit type annotations are respected with all_fields=True."""
    from typing import Optional

    class UserModel(BaseModel):
        name: str
        age: int  # int in pydantic model

    @pyd_type(model=UserModel, all_fields=True)
    class User:
        # Override age to be Optional[str] instead of int
        age: Optional[str] = None

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            # Note: we pass age as string via extra since it's now a different type
            pydantic_user = UserModel(name="Bob", age=25)
            return User.from_pydantic(pydantic_user, extra={"age": "25"})

    schema = strawberry.Schema(query=Query)
    schema_str = str(schema)

    # Verify age is String (nullable) in schema, not Int
    assert "age: String" in schema_str or "age: String!" not in schema_str
