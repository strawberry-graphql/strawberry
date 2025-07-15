"""Strawberry Pydantic integration.

This module provides first-class support for Pydantic models in Strawberry GraphQL.
You can directly decorate Pydantic BaseModel classes to create GraphQL types.

Example:
    @strawberry.pydantic.type
    class User(BaseModel):
        name: str
        age: int
"""

from .object_type import input, interface, type

__all__ = ["input", "interface", "type"]
