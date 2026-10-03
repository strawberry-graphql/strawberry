"""Object type decorators for Pydantic models in Strawberry GraphQL.

This module provides decorators to convert Pydantic BaseModel classes directly
into GraphQL types, inputs, and interfaces without requiring a separate wrapper class.
"""

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING, TypeVar, overload

from pydantic import BaseModel, RootModel

from strawberry.schema_directives import OneOf
from strawberry.types.base import StrawberryObjectDefinition
from strawberry.types.object_type import _get_interfaces
from strawberry.utils.str_converters import to_camel_case

from .conversion import build_pydantic_model, dump_pydantic_model
from .exceptions import (
    ModelAlreadyDecoratedError,
    NotAPydanticModelError,
    UnsupportedRootModelError,
)
from .fields import get_pydantic_fields, get_resolver_fields

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence


# The decorators return the class they're given, so type checkers keep the
# model's own type instead of a plain BaseModel
ModelT = TypeVar("ModelT", bound="BaseModel")


def _process_pydantic_type(
    cls: builtins.type[ModelT],
    *,
    name: str | None = None,
    is_input: bool = False,
    is_interface: bool = False,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    include_computed: bool = True,
) -> builtins.type[ModelT]:
    """Process a Pydantic BaseModel class and add GraphQL metadata.

    Args:
        cls: The Pydantic BaseModel class to process
        name: The GraphQL type name (defaults to class name)
        is_input: Whether this is an input type
        is_interface: Whether this is an interface type
        description: The GraphQL type description
        directives: GraphQL directives to apply
        include_computed: Whether to include computed fields

    Returns:
        The processed BaseModel class with GraphQL metadata
    """
    decorator = "input" if is_input else "interface" if is_interface else "type"

    if not (isinstance(cls, builtins.type) and issubclass(cls, BaseModel)):
        raise NotAPydanticModelError(cls, decorator)

    if issubclass(cls, RootModel):
        raise UnsupportedRootModelError(cls, decorator=decorator)

    if "__strawberry_definition__" in vars(cls):
        raise ModelAlreadyDecoratedError(cls, decorator)

    name = name or to_camel_case(cls.__name__)

    resolver_fields = get_resolver_fields(cls, is_input=is_input)
    resolver_field_names = {field.python_name for field in resolver_fields}

    fields = [
        # e.g. a computed field overridden by a resolver field in a subclass
        *(
            field
            for field in get_pydantic_fields(
                cls=cls,
                is_input=is_input,
                include_computed=include_computed,
            )
            if field.python_name not in resolver_field_names
        ),
        *resolver_fields,
    ]

    interfaces = _get_interfaces(cls)

    cls.__strawberry_definition__ = StrawberryObjectDefinition(  # type: ignore
        name=name,
        is_input=is_input,
        is_interface=is_interface,
        interfaces=interfaces,
        description=description,
        directives=directives,
        origin=cls,
        extend=False,
        fields=fields,
        # like `@strawberry.type`, resolvers can return objects that aren't
        # instances of the model, e.g. ORM rows, unless it defines `is_type_of`
        is_type_of=getattr(cls, "is_type_of", None),
        resolve_type=getattr(cls, "resolve_type", None),
        # also used by federation to build entities from their representations
        from_input=None if is_interface else build_pydantic_model,
        to_input=dump_pydantic_model if is_input else None,
    )

    return cls


@overload
def type(
    cls: builtins.type[ModelT],
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    include_computed: bool = True,
) -> builtins.type[ModelT]: ...


@overload
def type(
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    include_computed: bool = True,
) -> Callable[[builtins.type[ModelT]], builtins.type[ModelT]]: ...


def type(
    cls: builtins.type[ModelT] | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    include_computed: bool = True,
) -> builtins.type[ModelT] | Callable[[builtins.type[ModelT]], builtins.type[ModelT]]:
    """Decorator to convert a Pydantic BaseModel directly into a GraphQL type.

    This decorator allows you to use Pydantic models directly as GraphQL types
    without needing to create a separate wrapper class.

    Args:
        cls: The Pydantic BaseModel class to convert
        name: The GraphQL type name (defaults to class name)
        description: The GraphQL type description
        directives: GraphQL directives to apply to the type
        include_computed: Whether to include computed fields

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
            is_input=False,
            is_interface=False,
            description=description,
            directives=directives,
            include_computed=include_computed,
        )

    if cls is None:
        return wrap

    return wrap(cls)


@overload
def input(
    cls: builtins.type[ModelT],
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    one_of: bool | None = None,
) -> builtins.type[ModelT]: ...


@overload
def input(
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    one_of: bool | None = None,
) -> Callable[[builtins.type[ModelT]], builtins.type[ModelT]]: ...


def input(
    cls: builtins.type[ModelT] | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    one_of: bool | None = None,
) -> builtins.type[ModelT] | Callable[[builtins.type[ModelT]], builtins.type[ModelT]]:
    """Decorator to convert a Pydantic BaseModel directly into a GraphQL input type.

    This decorator allows you to use Pydantic models directly as GraphQL input types
    without needing to create a separate wrapper class.

    Args:
        cls: The Pydantic BaseModel class to convert
        name: The GraphQL input type name (defaults to class name)
        description: The GraphQL input type description
        directives: GraphQL directives to apply to the input type
        one_of: Whether the input type is a `oneOf` type

    Returns:
        The decorated BaseModel class with GraphQL input metadata

    Example:
        @strawberry.pydantic.input
        class CreateUserInput(BaseModel):
            name: str
            age: int

        # All fields from the Pydantic model will be included in the GraphQL input type
    """
    if one_of:
        directives = (*(directives or ()), OneOf())

    def wrap(cls: builtins.type[ModelT]) -> builtins.type[ModelT]:
        return _process_pydantic_type(
            cls,
            name=name,
            is_input=True,
            is_interface=False,
            description=description,
            directives=directives,
            include_computed=False,  # Input types don't need computed fields
        )

    if cls is None:
        return wrap

    return wrap(cls)


@overload
def interface(
    cls: builtins.type[ModelT],
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    include_computed: bool = True,
) -> builtins.type[ModelT]: ...


@overload
def interface(
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    include_computed: bool = True,
) -> Callable[[builtins.type[ModelT]], builtins.type[ModelT]]: ...


def interface(
    cls: builtins.type[ModelT] | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    include_computed: bool = True,
) -> builtins.type[ModelT] | Callable[[builtins.type[ModelT]], builtins.type[ModelT]]:
    """Decorator to convert a Pydantic BaseModel directly into a GraphQL interface.

    This decorator allows you to use Pydantic models directly as GraphQL interfaces
    without needing to create a separate wrapper class.

    Args:
        cls: The Pydantic BaseModel class to convert
        name: The GraphQL interface name (defaults to class name)
        description: The GraphQL interface description
        directives: GraphQL directives to apply to the interface
        include_computed: Whether to include computed fields

    Returns:
        The decorated BaseModel class with GraphQL interface metadata

    Example:
        @strawberry.pydantic.interface
        class Node(BaseModel):
            id: str
    """

    def wrap(cls: builtins.type[ModelT]) -> builtins.type[ModelT]:
        return _process_pydantic_type(
            cls,
            name=name,
            is_input=False,
            is_interface=True,
            description=description,
            directives=directives,
            include_computed=include_computed,
        )

    if cls is None:
        return wrap

    return wrap(cls)


__all__ = ["input", "interface", "type"]
