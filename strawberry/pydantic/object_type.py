"""Object type decorators for Pydantic models in Strawberry GraphQL.

This module provides decorators to convert Pydantic BaseModel classes directly
into GraphQL types, inputs, and interfaces without requiring a separate wrapper class.
"""

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING, TypeVar, overload

from pydantic import BaseModel

from strawberry.types.base import StrawberryObjectDefinition
from strawberry.utils.str_converters import to_camel_case

from .exceptions import ModelAlreadyDecoratedError, NotAPydanticModelError
from .fields import get_pydantic_fields

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence


# The decorators return the class they're given, so type checkers keep the
# model's own type instead of a plain BaseModel
ModelT = TypeVar("ModelT", bound="BaseModel")


def _process_pydantic_type(
    cls: builtins.type[ModelT],
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
) -> builtins.type[ModelT]:
    """Process a Pydantic BaseModel class and add GraphQL metadata.

    Args:
        cls: The Pydantic BaseModel class to process
        name: The GraphQL type name (defaults to class name)
        description: The GraphQL type description
        directives: GraphQL directives to apply

    Returns:
        The processed BaseModel class with GraphQL metadata
    """
    decorator = "type"

    if not (isinstance(cls, builtins.type) and issubclass(cls, BaseModel)):
        raise NotAPydanticModelError(cls, decorator)

    if "__strawberry_definition__" in vars(cls):
        raise ModelAlreadyDecoratedError(cls, decorator)

    name = name or to_camel_case(cls.__name__)

    cls.__strawberry_definition__ = StrawberryObjectDefinition(  # type: ignore
        name=name,
        is_input=False,
        is_interface=False,
        interfaces=[],
        description=description,
        directives=directives,
        origin=cls,
        extend=False,
        fields=get_pydantic_fields(cls),
        # like `@strawberry.type`, resolvers can return objects that aren't
        # instances of the model, e.g. ORM rows, unless it defines `is_type_of`
        is_type_of=getattr(cls, "is_type_of", None),
        resolve_type=getattr(cls, "resolve_type", None),
    )

    return cls


@overload
def type(
    cls: builtins.type[ModelT],
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
) -> builtins.type[ModelT]: ...


@overload
def type(
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
) -> Callable[[builtins.type[ModelT]], builtins.type[ModelT]]: ...


def type(
    cls: builtins.type[ModelT] | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
) -> builtins.type[ModelT] | Callable[[builtins.type[ModelT]], builtins.type[ModelT]]:
    """Decorator to convert a Pydantic BaseModel directly into a GraphQL type.

    This decorator allows you to use Pydantic models directly as GraphQL types
    without needing to create a separate wrapper class.

    Args:
        cls: The Pydantic BaseModel class to convert
        name: The GraphQL type name (defaults to class name)
        description: The GraphQL type description
        directives: GraphQL directives to apply to the type

    Returns:
        The decorated BaseModel class with GraphQL metadata

    Example:
        @strawberry.pydantic.type
        class User(BaseModel):
            name: str
            age: int

        # All fields from the Pydantic model will be included in the GraphQL type

        # You can also use strawberry.field() for field-level customization:
        @strawberry.pydantic.type
        class User(BaseModel):
            name: str
            age: Annotated[int, strawberry.field(directives=[SomeDirective()])]
    """

    def wrap(cls: builtins.type[ModelT]) -> builtins.type[ModelT]:
        return _process_pydantic_type(
            cls,
            name=name,
            description=description,
            directives=directives,
        )

    if cls is None:
        return wrap

    return wrap(cls)


__all__ = ["type"]
