"""Strawberry Pydantic integration.

This module provides first-class support for Pydantic models in Strawberry GraphQL.
You can directly decorate Pydantic BaseModel classes to create GraphQL types.

Example:
    @strawberry.pydantic.type
    class User(BaseModel):
        name: str
        age: int
"""

# must be imported first: checks that a supported pydantic is installed
from . import _requirements  # noqa: F401
from .error import (
    InputValidationError,
    PydanticValidationErrorHandler,
    ValidationError,
    ValidationIssue,
)
from .object_type import input, interface, type  # noqa: A004
from .resolver_field import field

__all__ = [
    "InputValidationError",
    "PydanticValidationErrorHandler",
    "ValidationError",
    "ValidationIssue",
    "field",
    "input",
    "interface",
    "type",
]
