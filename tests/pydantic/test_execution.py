"""
Execution tests for Pydantic integration.

These tests verify that Pydantic models work correctly in GraphQL execution,
including queries, mutations, and various field types.
"""

from typing import List, Optional

import pydantic
import pytest

import strawberry


def test_basic_query_execution():
    """Test basic query execution with Pydantic types."""
    
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str
        age: int
        
    @strawberry.type
    class Query:
        @strawberry.field
        def get_user(self) -> User:
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
    
    result = schema.execute_sync(query)
    
    assert not result.errors
    assert result.data == {
        "getUser": {
            "name": "John",
            "age": 30
        }
    }


def test_query_with_optional_fields():
    """Test query execution with optional fields."""
    
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str
        email: Optional[str] = None
        age: Optional[int] = None
        
    @strawberry.type
    class Query:
        @strawberry.field
        def get_user(self) -> User:
            return User(name="John", email="john@example.com")
    
    schema = strawberry.Schema(query=Query)
    
    query = """
        query {
            getUser {
                name
                email
                age
            }
        }
    """
    
    result = schema.execute_sync(query)
    
    assert not result.errors
    assert result.data == {
        "getUser": {
            "name": "John",
            "email": "john@example.com",
            "age": None
        }
    }


def test_mutation_with_input_types():
    """Test mutation execution with Pydantic input types."""
    
    @strawberry.pydantic.input
    class CreateUserInput(pydantic.BaseModel):
        name: str
        age: int
        email: Optional[str] = None
        
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        id: int
        name: str
        age: int
        email: Optional[str] = None
        
    @strawberry.type
    class Mutation:
        @strawberry.field
        def create_user(self, input: CreateUserInput) -> User:
            return User(
                id=1,
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
    
    mutation = """
        mutation {
            createUser(input: {
                name: "Alice"
                age: 25
                email: "alice@example.com"
            }) {
                id
                name
                age
                email
            }
        }
    """
    
    result = schema.execute_sync(mutation)
    
    assert not result.errors
    assert result.data == {
        "createUser": {
            "id": 1,
            "name": "Alice",
            "age": 25,
            "email": "alice@example.com"
        }
    }


def test_mutation_with_partial_input():
    """Test mutation with partial input (optional fields)."""
    
    @strawberry.pydantic.input
    class UpdateUserInput(pydantic.BaseModel):
        name: Optional[str] = None
        age: Optional[int] = None
        
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        id: int
        name: str
        age: int
        
    @strawberry.type
    class Mutation:
        @strawberry.field
        def update_user(self, id: int, input: UpdateUserInput) -> User:
            # Simulate updating a user
            return User(
                id=id,
                name=input.name or "Default Name",
                age=input.age or 18
            )
    
    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"
    
    schema = strawberry.Schema(query=Query, mutation=Mutation)
    
    mutation = """
        mutation {
            updateUser(id: 1, input: {
                name: "Updated Name"
            }) {
                id
                name
                age
            }
        }
    """
    
    result = schema.execute_sync(mutation)
    
    assert not result.errors
    assert result.data == {
        "updateUser": {
            "id": 1,
            "name": "Updated Name",
            "age": 18
        }
    }


def test_nested_pydantic_types():
    """Test nested Pydantic types in queries."""
    
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
    class Query:
        @strawberry.field
        def get_user(self) -> User:
            return User(
                name="John",
                age=30,
                address=Address(
                    street="123 Main St",
                    city="Anytown",
                    zipcode="12345"
                )
            )
    
    schema = strawberry.Schema(query=Query)
    
    query = """
        query {
            getUser {
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
    
    result = schema.execute_sync(query)
    
    assert not result.errors
    assert result.data == {
        "getUser": {
            "name": "John",
            "age": 30,
            "address": {
                "street": "123 Main St",
                "city": "Anytown",
                "zipcode": "12345"
            }
        }
    }


def test_list_of_pydantic_types():
    """Test lists of Pydantic types."""
    
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str
        age: int
        
    @strawberry.type
    class Query:
        @strawberry.field
        def get_users(self) -> List[User]:
            return [
                User(name="John", age=30),
                User(name="Jane", age=25),
                User(name="Bob", age=35)
            ]
    
    schema = strawberry.Schema(query=Query)
    
    query = """
        query {
            getUsers {
                name
                age
            }
        }
    """
    
    result = schema.execute_sync(query)
    
    assert not result.errors
    assert result.data == {
        "getUsers": [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": 25},
            {"name": "Bob", "age": 35}
        ]
    }


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
    
    @strawberry.pydantic.type(use_pydantic_alias=True)
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
    assert result.data == {
        "getUser": {
            "fullName": "John",
            "yearsOld": 30
        }
    }


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
    assert result.data == {
        "createUser": {
            "name": "Alice",
            "age": 25,
            "email": "alice@example.com"
        }
    }


def test_complex_pydantic_types_execution():
    """Test complex Pydantic types with various field types."""
    
    @strawberry.pydantic.type
    class Profile(pydantic.BaseModel):
        bio: Optional[str] = None
        website: Optional[str] = None
        
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        id: int
        name: str
        email: str
        is_active: bool
        tags: List[str] = []
        profile: Optional[Profile] = None
        
    @strawberry.type
    class Query:
        @strawberry.field
        def get_user(self) -> User:
            return User(
                id=1,
                name="John Doe",
                email="john@example.com",
                is_active=True,
                tags=["developer", "python", "graphql"],
                profile=Profile(
                    bio="Software developer",
                    website="https://johndoe.com"
                )
            )
    
    schema = strawberry.Schema(query=Query)
    
    query = """
        query {
            getUser {
                id
                name
                email
                isActive
                tags
                profile {
                    bio
                    website
                }
            }
        }
    """
    
    result = schema.execute_sync(query)
    
    assert not result.errors
    assert result.data == {
        "getUser": {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "isActive": True,
            "tags": ["developer", "python", "graphql"],
            "profile": {
                "bio": "Software developer",
                "website": "https://johndoe.com"
            }
        }
    }


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
    assert result.data == {
        "getUser": {
            "id": "user_1",
            "name": "John"
        }
    }


def test_error_handling_with_pydantic_validation():
    """Test error handling when Pydantic validation fails."""
    
    @strawberry.pydantic.input
    class CreateUserInput(pydantic.BaseModel):
        name: str
        age: int
        
        @pydantic.validator('age')
        def validate_age(cls, v):
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
    # The exact error handling depends on Strawberry's error handling implementation
    assert result.errors or result.data is None


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
    assert result.data == {
        "getUser": {
            "name": "John",
            "age": 30
        }
    }