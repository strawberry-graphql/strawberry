from typing import Annotated, Optional

import pydantic
from inline_snapshot import snapshot

import strawberry
from strawberry.types.base import get_object_definition


def test_basic_input_type():
    """Test that @strawberry.pydantic.input works."""

    @strawberry.pydantic.input
    class CreateUserInput(pydantic.BaseModel):
        age: int
        name: str

    definition = get_object_definition(CreateUserInput, strict=True)

    assert definition.name == "CreateUserInput"
    assert definition.is_input is True
    assert len(definition.fields) == 2


def test_input_type_with_valid_data():
    """Test input type with various valid data scenarios."""

    @strawberry.pydantic.input
    class UserInput(pydantic.BaseModel):
        name: str
        age: int
        email: str
        is_active: bool = True
        tags: list[str] = []

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        id: int
        name: str
        age: int
        email: str
        is_active: bool
        tags: list[str]

    @strawberry.type
    class Mutation:
        @strawberry.field
        def create_user(self, input: UserInput) -> User:
            return User(
                id=1,
                name=input.name,
                age=input.age,
                email=input.email,
                is_active=input.is_active,
                tags=input.tags,
            )

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test with all fields provided
    mutation = """
        mutation {
            createUser(input: {
                name: "John Doe"
                age: 30
                email: "john@example.com"
                isActive: false
                tags: ["developer", "python"]
            }) {
                id
                name
                age
                email
                isActive
                tags
            }
        }
    """

    result = schema.execute_sync(mutation)

    assert not result.errors
    assert result.data == snapshot(
        {
            "createUser": {
                "id": 1,
                "name": "John Doe",
                "age": 30,
                "email": "john@example.com",
                "isActive": False,
                "tags": ["developer", "python"],
            }
        }
    )

    # Test with default values
    mutation_defaults = """
        mutation {
            createUser(input: {
                name: "Jane Doe"
                age: 25
                email: "jane@example.com"
            }) {
                id
                name
                age
                email
                isActive
                tags
            }
        }
    """

    result = schema.execute_sync(mutation_defaults)

    assert not result.errors
    assert result.data == snapshot(
        {
            "createUser": {
                "id": 1,
                "name": "Jane Doe",
                "age": 25,
                "email": "jane@example.com",
                "isActive": True,  # default value
                "tags": [],  # default value
            }
        }
    )


def test_input_type_with_invalid_email():
    """Test input type with invalid email format."""

    @strawberry.pydantic.input
    class UserInput(pydantic.BaseModel):
        name: Annotated[str, pydantic.Field(min_length=2, max_length=50)]
        age: Annotated[int, pydantic.Field(ge=0, le=150)]
        email: Annotated[str, pydantic.Field(pattern=r"^[^@]+@[^@]+\.[^@]+$")]

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str
        age: int
        email: str

    @strawberry.type
    class Mutation:
        @strawberry.field
        def create_user(self, input: UserInput) -> User:
            return User(name=input.name, age=input.age, email=input.email)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test with invalid email
    mutation_invalid_email = """
        mutation {
            createUser(input: {
                name: "John"
                age: 30
                email: "invalid-email"
            }) {
                name
                age
                email
            }
        }
    """

    result = schema.execute_sync(mutation_invalid_email)
    assert result.errors is not None
    assert len(result.errors) == 1
    error_message = result.errors[0].message
    assert "1 validation error for UserInput" in error_message
    assert "email" in error_message
    assert "string_pattern_mismatch" in error_message


def test_input_type_with_invalid_name_length():
    """Test input type with name validation errors."""

    @strawberry.pydantic.input
    class UserInput(pydantic.BaseModel):
        name: Annotated[str, pydantic.Field(min_length=2, max_length=50)]
        age: Annotated[int, pydantic.Field(ge=0, le=150)]
        email: Annotated[str, pydantic.Field(pattern=r"^[^@]+@[^@]+\.[^@]+$")]

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str
        age: int
        email: str

    @strawberry.type
    class Mutation:
        @strawberry.field
        def create_user(self, input: UserInput) -> User:
            return User(name=input.name, age=input.age, email=input.email)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test with name too short
    mutation_short_name = """
        mutation {
            createUser(input: {
                name: "J"
                age: 30
                email: "john@example.com"
            }) {
                name
                age
                email
            }
        }
    """

    result = schema.execute_sync(mutation_short_name)
    assert result.errors is not None
    assert len(result.errors) == 1
    error_message = result.errors[0].message
    assert "1 validation error for UserInput" in error_message
    assert "name" in error_message
    assert "string_too_short" in error_message


def test_input_type_with_invalid_age_range():
    """Test input type with age validation errors."""

    @strawberry.pydantic.input
    class UserInput(pydantic.BaseModel):
        name: Annotated[str, pydantic.Field(min_length=2, max_length=50)]
        age: Annotated[int, pydantic.Field(ge=0, le=150)]
        email: Annotated[str, pydantic.Field(pattern=r"^[^@]+@[^@]+\.[^@]+$")]

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str
        age: int
        email: str

    @strawberry.type
    class Mutation:
        @strawberry.field
        def create_user(self, input: UserInput) -> User:
            return User(name=input.name, age=input.age, email=input.email)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test with age out of range (negative)
    mutation_negative_age = """
        mutation {
            createUser(input: {
                name: "John"
                age: -5
                email: "john@example.com"
            }) {
                name
                age
                email
            }
        }
    """

    result = schema.execute_sync(mutation_negative_age)
    assert result.errors is not None
    assert len(result.errors) == 1
    error_message = result.errors[0].message
    assert "1 validation error for UserInput" in error_message
    assert "age" in error_message
    assert "greater_than_equal" in error_message

    # Test with age out of range (too high)
    mutation_high_age = """
        mutation {
            createUser(input: {
                name: "John"
                age: 200
                email: "john@example.com"
            }) {
                name
                age
                email
            }
        }
    """

    result = schema.execute_sync(mutation_high_age)
    assert result.errors is not None
    assert len(result.errors) == 1
    error_message = result.errors[0].message
    assert "1 validation error for UserInput" in error_message
    assert "age" in error_message
    assert "less_than_equal" in error_message


def test_nested_input_types_with_validation():
    """Test nested input types with validation."""

    @strawberry.pydantic.input
    class AddressInput(pydantic.BaseModel):
        street: Annotated[str, pydantic.Field(min_length=5)]
        city: Annotated[str, pydantic.Field(min_length=2)]
        zipcode: Annotated[str, pydantic.Field(pattern=r"^\d{5}$")]

    @strawberry.pydantic.input
    class UserInput(pydantic.BaseModel):
        name: str
        age: Annotated[int, pydantic.Field(ge=18)]  # Must be 18 or older
        address: AddressInput

    @strawberry.pydantic.type
    class Address(pydantic.BaseModel):
        street: str
        city: str
        zipcode: str

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str
        age: int
        address: Address

    @strawberry.type
    class Mutation:
        @strawberry.field
        def create_user(self, input: UserInput) -> User:
            return User(
                name=input.name,
                age=input.age,
                address=Address(
                    street=input.address.street,
                    city=input.address.city,
                    zipcode=input.address.zipcode,
                ),
            )

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test with valid nested data
    mutation_valid = """
        mutation {
            createUser(input: {
                name: "Alice"
                age: 25
                address: {
                    street: "123 Main Street"
                    city: "New York"
                    zipcode: "12345"
                }
            }) {
                name
                age
                address {
                    street
                    city
                    zipcode
                }
            }
        }
    """

    result = schema.execute_sync(mutation_valid)

    assert not result.errors
    assert result.data == snapshot(
        {
            "createUser": {
                "name": "Alice",
                "age": 25,
                "address": {
                    "street": "123 Main Street",
                    "city": "New York",
                    "zipcode": "12345",
                },
            }
        }
    )

    # Test with invalid nested data (invalid zipcode)
    mutation_invalid_zip = """
        mutation {
            createUser(input: {
                name: "Bob"
                age: 30
                address: {
                    street: "456 Elm Street"
                    city: "Boston"
                    zipcode: "1234"  # Too short
                }
            }) {
                name
                age
                address {
                    street
                    city
                    zipcode
                }
            }
        }
    """

    result = schema.execute_sync(mutation_invalid_zip)
    assert result.errors is not None
    assert len(result.errors) == 1
    error_message = result.errors[0].message
    assert "1 validation error for AddressInput" in error_message
    assert "zipcode" in error_message
    assert "string_pattern_mismatch" in error_message

    # Test with invalid nested data (underage)
    mutation_underage = """
        mutation {
            createUser(input: {
                name: "Charlie"
                age: 16  # Under 18
                address: {
                    street: "789 Oak Street"
                    city: "Chicago"
                    zipcode: "60601"
                }
            }) {
                name
                age
                address {
                    street
                    city
                    zipcode
                }
            }
        }
    """

    result = schema.execute_sync(mutation_underage)
    assert result.errors is not None
    assert len(result.errors) == 1
    error_message = result.errors[0].message
    assert "1 validation error for UserInput" in error_message
    assert "age" in error_message
    assert "greater_than_equal" in error_message


def test_input_type_with_custom_validators():
    """Test input types with custom Pydantic validators."""

    @strawberry.pydantic.input
    class RegistrationInput(pydantic.BaseModel):
        username: str
        password: str
        confirm_password: str
        age: int

        @pydantic.field_validator("username")
        @classmethod
        def username_alphanumeric(cls, v: str) -> str:
            if not v.isalnum():
                raise ValueError("Username must be alphanumeric")
            if len(v) < 3:
                raise ValueError("Username must be at least 3 characters long")
            return v

        @pydantic.field_validator("password")
        @classmethod
        def password_strength(cls, v: str) -> str:
            if len(v) < 8:
                raise ValueError("Password must be at least 8 characters long")
            if not any(c.isupper() for c in v):
                raise ValueError("Password must contain at least one uppercase letter")
            if not any(c.isdigit() for c in v):
                raise ValueError("Password must contain at least one digit")
            return v

        @pydantic.field_validator("confirm_password")
        @classmethod
        def passwords_match(cls, v: str, info: pydantic.ValidationInfo) -> str:
            if "password" in info.data and v != info.data["password"]:
                raise ValueError("Passwords do not match")
            return v

        @pydantic.field_validator("age")
        @classmethod
        def age_requirement(cls, v: int) -> int:
            if v < 13:
                raise ValueError("Must be at least 13 years old")
            return v

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        username: str
        age: int

    @strawberry.type
    class Mutation:
        @strawberry.field
        def register(self, input: RegistrationInput) -> User:
            return User(username=input.username, age=input.age)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test with valid input
    mutation_valid = """
        mutation {
            register(input: {
                username: "john123"
                password: "SecurePass123"
                confirmPassword: "SecurePass123"
                age: 25
            }) {
                username
                age
            }
        }
    """

    result = schema.execute_sync(mutation_valid)

    assert not result.errors
    assert result.data == snapshot({"register": {"username": "john123", "age": 25}})

    # Test with non-alphanumeric username
    mutation_invalid_username = """
        mutation {
            register(input: {
                username: "john@123"
                password: "SecurePass123"
                confirmPassword: "SecurePass123"
                age: 25
            }) {
                username
                age
            }
        }
    """

    result = schema.execute_sync(mutation_invalid_username)
    assert result.errors is not None
    assert len(result.errors) == 1
    error_message = result.errors[0].message
    assert "1 validation error for RegistrationInput" in error_message
    assert "username" in error_message
    assert "Username must be alphanumeric" in error_message

    # Test with weak password
    mutation_weak_password = """
        mutation {
            register(input: {
                username: "john123"
                password: "weak"
                confirmPassword: "weak"
                age: 25
            }) {
                username
                age
            }
        }
    """

    result = schema.execute_sync(mutation_weak_password)
    assert result.errors is not None
    assert len(result.errors) == 1
    error_message = result.errors[0].message
    assert "1 validation error for RegistrationInput" in error_message
    assert "password" in error_message
    assert "Password must be at least 8 characters long" in error_message

    # Test with mismatched passwords
    mutation_mismatch_password = """
        mutation {
            register(input: {
                username: "john123"
                password: "SecurePass123"
                confirmPassword: "DifferentPass123"
                age: 25
            }) {
                username
                age
            }
        }
    """

    result = schema.execute_sync(mutation_mismatch_password)
    assert result.errors is not None
    assert len(result.errors) == 1
    error_message = result.errors[0].message
    assert "1 validation error for RegistrationInput" in error_message
    assert "confirm_password" in error_message
    assert "Passwords do not match" in error_message

    # Test with underage user
    mutation_underage = """
        mutation {
            register(input: {
                username: "kid123"
                password: "SecurePass123"
                confirmPassword: "SecurePass123"
                age: 10
            }) {
                username
                age
            }
        }
    """

    result = schema.execute_sync(mutation_underage)
    assert result.errors is not None
    assert len(result.errors) == 1
    error_message = result.errors[0].message
    assert "1 validation error for RegistrationInput" in error_message
    assert "age" in error_message
    assert "Must be at least 13 years old" in error_message


def test_input_type_with_optional_fields_and_validation():
    """Test input types with optional fields and validation."""

    @strawberry.pydantic.input
    class UpdateProfileInput(pydantic.BaseModel):
        bio: Annotated[Optional[str], pydantic.Field(None, max_length=200)]
        website: Annotated[Optional[str], pydantic.Field(None, pattern=r"^https?://.*")]
        age: Annotated[Optional[int], pydantic.Field(None, ge=0, le=150)]

    @strawberry.pydantic.type
    class Profile(pydantic.BaseModel):
        bio: Optional[str] = None
        website: Optional[str] = None
        age: Optional[int] = None

    @strawberry.type
    class Mutation:
        @strawberry.field
        def update_profile(self, input: UpdateProfileInput) -> Profile:
            return Profile(bio=input.bio, website=input.website, age=input.age)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test with all valid optional fields
    mutation_all_fields = """
        mutation {
            updateProfile(input: {
                bio: "Software developer"
                website: "https://example.com"
                age: 30
            }) {
                bio
                website
                age
            }
        }
    """

    result = schema.execute_sync(mutation_all_fields)

    assert not result.errors
    assert result.data == snapshot(
        {
            "updateProfile": {
                "bio": "Software developer",
                "website": "https://example.com",
                "age": 30,
            }
        }
    )

    # Test with only some fields
    mutation_partial = """
        mutation {
            updateProfile(input: {
                bio: "Just a bio"
            }) {
                bio
                website
                age
            }
        }
    """

    result = schema.execute_sync(mutation_partial)

    assert not result.errors
    assert result.data == snapshot(
        {"updateProfile": {"bio": "Just a bio", "website": None, "age": None}}
    )

    # Test with invalid website URL
    mutation_invalid_url = """
        mutation {
            updateProfile(input: {
                website: "not-a-url"
            }) {
                bio
                website
                age
            }
        }
    """

    result = schema.execute_sync(mutation_invalid_url)
    assert result.errors is not None
    assert len(result.errors) == 1
    error_message = result.errors[0].message
    assert "1 validation error for UpdateProfileInput" in error_message
    assert "website" in error_message
    assert "string_pattern_mismatch" in error_message

    # Test with bio too long
    long_bio = "x" * 201
    mutation_long_bio = f"""
        mutation {{
            updateProfile(input: {{
                bio: "{long_bio}"
            }}) {{
                bio
                website
                age
            }}
        }}
    """

    result = schema.execute_sync(mutation_long_bio)
    assert result.errors is not None
    assert len(result.errors) == 1
    error_message = result.errors[0].message
    assert "1 validation error for UpdateProfileInput" in error_message
    assert "bio" in error_message
    assert "string_too_long" in error_message
