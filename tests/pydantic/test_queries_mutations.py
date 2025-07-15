"""
Query and mutation execution tests for Pydantic integration.

These tests verify that Pydantic models work correctly in GraphQL queries and mutations.
"""

from typing import List, Optional

import pydantic
import pytest

import strawberry
from inline_snapshot import snapshot


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
    assert result.data == snapshot({
        "getUser": {
            "name": "John",
            "age": 30
        }
    })


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
    assert result.data == snapshot({
        "getUser": {
            "name": "John",
            "email": "john@example.com",
            "age": None
        }
    })


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
    assert result.data == snapshot({
        "createUser": {
            "id": 1,
            "name": "Alice",
            "age": 25,
            "email": "alice@example.com"
        }
    })


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
    assert result.data == snapshot({
        "updateUser": {
            "id": 1,
            "name": "Updated Name",
            "age": 18
        }
    })