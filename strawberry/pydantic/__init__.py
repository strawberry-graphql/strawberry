"""Strawberry Pydantic integration.

This module provides first-class support for Pydantic models in Strawberry GraphQL.
You can directly decorate Pydantic BaseModel classes to create GraphQL types.

Example:
    @strawberry.pydantic.type
    class User(BaseModel):
        name: str
        age: int
"""

from .error import Error
from .object_type import input as input_decorator
from .object_type import interface
from .object_type import type as type_decorator

# Re-export with proper names
input = input_decorator
type = type_decorator

__all__ = ["Error", "input", "interface", "type"]
