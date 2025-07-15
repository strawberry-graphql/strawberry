"""
Special features tests for Pydantic integration.

These tests verify special features like field descriptions, aliases, private fields, etc.
"""

from typing import List, Optional

import pydantic
import pytest

import strawberry
from inline_snapshot import snapshot


def test_pydantic_field_descriptions_in_schema():
    """Test that Pydantic field descriptions appear in the schema."""
    
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str = pydantic.Field(description="The user's full name")
        age: int = pydantic.Field(description="The user's age in years")
        
    @strawberry.type
    class Query:
        @strawberry.field
        def get_user(self) -> User:
            return User(name="John", age=30)
    
    schema = strawberry.Schema(query=Query)
    
    # Check that the schema includes field descriptions
    schema_str = str(schema)
    assert "The user's full name" in schema_str
    assert "The user's age in years" in schema_str


def test_pydantic_field_aliases_in_execution():
    """Test that Pydantic field aliases work in GraphQL execution."""
    
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str = pydantic.Field(alias="fullName")
        age: int = pydantic.Field(alias="yearsOld")
        
    @strawberry.type
    class Query:
        @strawberry.field
        def get_user(self) -> User:
            # When using aliases, we need to create the User with the aliased field names
            return User(fullName="John", yearsOld=30)
    
    schema = strawberry.Schema(query=Query)
    
    # Query using the aliased field names
    query = """
        query {
            getUser {
                fullName
                yearsOld
            }
        }
    """
    
    result = schema.execute_sync(query)
    
    assert not result.errors
    assert result.data == snapshot({
        "getUser": {
            "fullName": "John",
            "yearsOld": 30
        }
    })


def test_strawberry_private_fields_not_in_schema():
    """Test that strawberry.Private fields are not exposed in GraphQL schema."""
    
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        id: int
        name: str
        password: strawberry.Private[str]
        
    @strawberry.type
    class Query:
        @strawberry.field
        def get_user(self) -> User:
            return User(id=1, name="John", password="secret123")
    
    schema = strawberry.Schema(query=Query)
    
    # Check that password field is not in the schema
    schema_str = str(schema)
    assert "password" not in schema_str
    assert "id: Int!" in schema_str
    assert "name: String!" in schema_str
    
    # Test that we can query the exposed fields
    query = """
        query {
            getUser {
                id
                name
            }
        }
    """
    
    result = schema.execute_sync(query)
    
    assert not result.errors
    assert result.data == snapshot({
        "getUser": {
            "id": 1,
            "name": "John"
        }
    })
    
    # Test that querying the private field fails
    query_with_private = """
        query {
            getUser {
                id
                name
                password
            }
        }
    """
    
    result = schema.execute_sync(query_with_private)
    assert result.errors
    assert len(result.errors) == 1
    assert result.errors[0].message == snapshot("Cannot query field 'password' on type 'User'.")


def test_pydantic_validation_integration():
    """Test that Pydantic validation works with GraphQL inputs."""
    
    @strawberry.pydantic.input
    class CreateUserInput(pydantic.BaseModel):
        name: str
        age: int
        email: str = pydantic.Field(pattern=r'^[^@]+@[^@]+\.[^@]+$')
        
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str
        age: int
        email: str
        
    @strawberry.type
    class Mutation:
        @strawberry.field
        def create_user(self, input: CreateUserInput) -> User:
            return User(
                name=input.name,
                age=input.age,
                email=input.email
            )
    
    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"
    
    schema = strawberry.Schema(query=Query, mutation=Mutation)
    
    # Test with valid input
    mutation = """
        mutation {
            createUser(input: {
                name: "Alice"
                age: 25
                email: "alice@example.com"
            }) {
                name
                age
                email
            }
        }
    """
    
    result = schema.execute_sync(mutation)
    
    assert not result.errors
    assert result.data == snapshot({
        "createUser": {
            "name": "Alice",
            "age": 25,
            "email": "alice@example.com"
        }
    })


def test_error_handling_with_pydantic_validation():
    """Test error handling when Pydantic validation fails."""
    
    @strawberry.pydantic.input
    class CreateUserInput(pydantic.BaseModel):
        name: str
        age: int
        
        @pydantic.field_validator('age')
        @classmethod
        def validate_age(cls, v: int) -> int:
            if v < 0:
                raise ValueError('Age must be non-negative')
            return v
    
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str
        age: int
        
    @strawberry.type
    class Mutation:
        @strawberry.field
        def create_user(self, input: CreateUserInput) -> User:
            return User(name=input.name, age=input.age)
    
    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"
    
    schema = strawberry.Schema(query=Query, mutation=Mutation)
    
    # Test with invalid input (negative age)
    mutation = """
        mutation {
            createUser(input: {
                name: "Alice"
                age: -5
            }) {
                name
                age
            }
        }
    """
    
    result = schema.execute_sync(mutation)
    
    # Should handle validation error gracefully
    assert result.errors is not None
    assert len(result.errors) == 1
    assert result.errors[0].message == snapshot("""\
1 validation error for CreateUserInput
age
  Value error, Age must be non-negative [type=value_error, input_value=-5, input_type=int]
    For further information visit https://errors.pydantic.dev/2.11/v/value_error\
""")


def test_pydantic_interface_basic():
    """Test basic Pydantic interface functionality."""
    
    @strawberry.pydantic.interface
    class Node(pydantic.BaseModel):
        id: str
        
    # Interface requires implementing types for proper execution
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        id: str
        name: str
        
    @strawberry.type
    class Query:
        @strawberry.field
        def get_user(self) -> User:
            return User(id="user_1", name="John")
    
    schema = strawberry.Schema(query=Query)
    
    query = """
        query {
            getUser {
                id
                name
            }
        }
    """
    
    result = schema.execute_sync(query)
    
    assert not result.errors
    assert result.data == snapshot({
        "getUser": {
            "id": "user_1",
            "name": "John"
        }
    })


@pytest.mark.asyncio
async def test_async_execution_with_pydantic():
    """Test async execution with Pydantic types."""
    
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str
        age: int
        
    @strawberry.type
    class Query:
        @strawberry.field
        async def get_user(self) -> User:
            # Simulate async operation
            return User(name="John", age=30)
    
    schema = strawberry.Schema(query=Query)
    
    query = """
        query {
            getUser {
                name
                age
            }
        }
    """
    
    result = await schema.execute(query)
    
    assert not result.errors
    assert result.data == snapshot({
        "getUser": {
            "name": "John",
            "age": 30
        }
    })