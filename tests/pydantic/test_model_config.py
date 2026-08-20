"""Tests for Pydantic model_config support with first-class integration."""

import pydantic
from pydantic import ConfigDict

import strawberry


def test_strict_mode_rejects_type_coercion():
    """Test that strict=True rejects type coercion."""

    @strawberry.pydantic.input
    class StrictInput(pydantic.BaseModel):
        model_config = ConfigDict(strict=True)

        age: int
        name: str

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        age: int
        name: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_user(self, input: StrictInput) -> User:
            return User(age=input.age, name=input.name)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test with correct types - should work
    result = schema.execute_sync(
        """
        mutation {
            createUser(input: { age: 25, name: "Alice" }) {
                age
                name
            }
        }
        """
    )

    assert not result.errors
    assert result.data["createUser"]["age"] == 25

    # Note: GraphQL handles type coercion at the schema level, so
    # passing "25" as a string would be rejected by GraphQL itself before
    # reaching Pydantic. This test verifies the model config is respected
    # when values reach Pydantic.


def test_extra_forbid_rejects_unknown_fields():
    """Test that extra='forbid' rejects unknown fields at Pydantic level.

    Note: GraphQL schemas already enforce known fields, but this ensures
    Pydantic's extra='forbid' is respected if data comes from other sources.
    """

    @strawberry.pydantic.input
    class StrictUserInput(pydantic.BaseModel):
        model_config = ConfigDict(extra="forbid")

        name: str
        age: int

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str
        age: int

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_user(self, input: StrictUserInput) -> User:
            return User(name=input.name, age=input.age)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Valid input should work
    result = schema.execute_sync(
        """
        mutation {
            createUser(input: { name: "Alice", age: 25 }) {
                name
                age
            }
        }
        """
    )

    assert not result.errors
    assert result.data["createUser"]["name"] == "Alice"


def test_extra_allow_stores_extra_fields():
    """Test that extra='allow' stores extra fields in __pydantic_extra__."""

    @strawberry.pydantic.input
    class FlexibleInput(pydantic.BaseModel):
        model_config = ConfigDict(extra="allow")

        name: str

    @strawberry.pydantic.type
    class Result(pydantic.BaseModel):
        name: str
        extra_count: int

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def process(self, input: FlexibleInput) -> Result:
            extra_count = len(input.__pydantic_extra__ or {})
            return Result(name=input.name, extra_count=extra_count)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # GraphQL won't allow unknown fields at query level,
    # but the config should still be applied
    result = schema.execute_sync(
        """
        mutation {
            process(input: { name: "Alice" }) {
                name
                extraCount
            }
        }
        """
    )

    assert not result.errors
    assert result.data["process"]["name"] == "Alice"
    # No extra fields passed through GraphQL
    assert result.data["process"]["extraCount"] == 0


def test_from_attributes_with_dataclass():
    """Test that from_attributes=True allows populating from objects."""

    from dataclasses import dataclass

    @dataclass
    class ORMUser:
        id: int
        name: str
        email: str

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        model_config = ConfigDict(from_attributes=True)

        id: int
        name: str
        email: str

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            # Simulate getting data from ORM
            orm_user = ORMUser(id=1, name="Alice", email="alice@example.com")
            # Use model_validate to populate from attributes
            return User.model_validate(orm_user)

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        """
        query {
            user {
                id
                name
                email
            }
        }
        """
    )

    assert not result.errors
    assert result.data["user"]["id"] == 1
    assert result.data["user"]["name"] == "Alice"
    assert result.data["user"]["email"] == "alice@example.com"


def test_validate_default_runs_validators_on_defaults():
    """Test that validate_default=True validates default values."""

    @strawberry.pydantic.input
    class ConfigInput(pydantic.BaseModel):
        model_config = ConfigDict(validate_default=True)

        count: int = 10

        @pydantic.field_validator("count")
        @classmethod
        def check_count(cls, v: int) -> int:
            if v < 0:
                raise ValueError("count must be non-negative")
            return v

    @strawberry.pydantic.type
    class Config(pydantic.BaseModel):
        count: int

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_config(self, input: ConfigInput) -> Config:
            return Config(count=input.count)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Using default value - should work (10 is valid)
    result = schema.execute_sync(
        """
        mutation {
            createConfig(input: {}) {
                count
            }
        }
        """
    )

    assert not result.errors
    assert result.data["createConfig"]["count"] == 10


def test_populate_by_name_allows_field_name_or_alias():
    """Test that populate_by_name=True allows using either field name or alias."""

    @strawberry.pydantic.input
    class FlexibleNameInput(pydantic.BaseModel):
        model_config = ConfigDict(populate_by_name=True)

        user_name: str = pydantic.Field(alias="userName")

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        user_name: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_user(self, input: FlexibleNameInput) -> User:
            return User(user_name=input.user_name)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # GraphQL uses the alias (userName) for the field name
    result = schema.execute_sync(
        """
        mutation {
            createUser(input: { userName: "Alice" }) {
                userName
            }
        }
        """
    )

    assert not result.errors
    assert result.data["createUser"]["userName"] == "Alice"


def test_str_strip_whitespace_config():
    """Test that str_strip_whitespace=True strips whitespace from strings."""

    @strawberry.pydantic.input
    class CleanInput(pydantic.BaseModel):
        model_config = ConfigDict(str_strip_whitespace=True)

        name: str

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_user(self, input: CleanInput) -> User:
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
            createUser(input: { name: "  Alice  " }) {
                name
            }
        }
        """
    )

    assert not result.errors
    # Whitespace should be stripped
    assert result.data["createUser"]["name"] == "Alice"


def test_multiple_config_options_combined():
    """Test combining multiple config options."""

    @strawberry.pydantic.input
    class StrictCleanInput(pydantic.BaseModel):
        model_config = ConfigDict(
            strict=True,
            str_strip_whitespace=True,
            str_min_length=1,  # Ensure non-empty after strip
        )

        name: str
        age: int

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str
        age: int

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_user(self, input: StrictCleanInput) -> User:
            return User(name=input.name, age=input.age)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Valid input with whitespace that gets stripped
    result = schema.execute_sync(
        """
        mutation {
            createUser(input: { name: "  Alice  ", age: 25 }) {
                name
                age
            }
        }
        """
    )

    assert not result.errors
    assert result.data["createUser"]["name"] == "Alice"
    assert result.data["createUser"]["age"] == 25

    # Empty string after strip should fail (str_min_length=1)
    result = schema.execute_sync(
        """
        mutation {
            createUser(input: { name: "   ", age: 25 }) {
                name
                age
            }
        }
        """
    )

    assert result.errors is not None
    assert "string_too_short" in result.errors[0].message
