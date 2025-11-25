"""Object type decorators for Pydantic models in Strawberry GraphQL.

This module provides decorators to convert Pydantic BaseModel classes directly
into GraphQL types, inputs, and interfaces without requiring a separate wrapper class.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, overload

if TYPE_CHECKING:
    import builtins
    from collections.abc import Callable, Sequence

    from graphql import GraphQLResolveInfo
    from pydantic import BaseModel

from strawberry.types.base import StrawberryObjectDefinition
from strawberry.types.cast import get_strawberry_type_cast
from strawberry.utils.str_converters import to_camel_case

from .fields import _get_pydantic_fields


def _get_interfaces(cls: builtins.type[Any]) -> list[StrawberryObjectDefinition]:
    """Extract interfaces from a class's inheritance hierarchy."""
    interfaces: list[StrawberryObjectDefinition] = []

    for base in cls.__mro__[1:]:  # Exclude current class
        if hasattr(base, "__strawberry_definition__"):
            type_definition = base.__strawberry_definition__
            if type_definition.is_interface:
                interfaces.append(type_definition)

    return interfaces


def _process_pydantic_type(
    cls: builtins.type[BaseModel],
    *,
    name: str | None = None,
    is_input: bool = False,
    is_interface: bool = False,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    include_computed: bool = False,
) -> builtins.type[BaseModel]:
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
    # Get the GraphQL type name
    name = name or to_camel_case(cls.__name__)

    # Extract fields using our custom function
    # All fields from the Pydantic model are included by default, except strawberry.Private fields
    fields = _get_pydantic_fields(
        cls=cls,
        original_type_annotations={},
        is_input=is_input,
        include_computed=include_computed,
    )

    # Get interfaces from inheritance hierarchy
    interfaces = _get_interfaces(cls)

    # Create the is_type_of method for proper type resolution
    def is_type_of(obj: Any, _info: GraphQLResolveInfo) -> bool:
        if (type_cast := get_strawberry_type_cast(obj)) is not None:
            return type_cast is cls
        return isinstance(obj, cls)

    # Create the GraphQL type definition
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
        is_type_of=is_type_of,
        resolve_type=getattr(cls, "resolve_type", None),
    )

    # Add the is_type_of method to the class for testing purposes
    cls.is_type_of = is_type_of  # type: ignore

    return cls


@overload
def type(
    cls: builtins.type[BaseModel],
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    include_computed: bool = False,
) -> builtins.type[BaseModel]: ...


@overload
def type(
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    include_computed: bool = False,
) -> Callable[[builtins.type[BaseModel]], builtins.type[BaseModel]]: ...


def type(
    cls: builtins.type[BaseModel] | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    include_computed: bool = False,
) -> (
    builtins.type[BaseModel]
    | Callable[[builtins.type[BaseModel]], builtins.type[BaseModel]]
):
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
            age: int = strawberry.field(directives=[SomeDirective()])
    """

    def wrap(cls: builtins.type[BaseModel]) -> builtins.type[BaseModel]:
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
    cls: builtins.type[BaseModel],
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
) -> builtins.type[BaseModel]: ...


@overload
def input(
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
) -> Callable[[builtins.type[BaseModel]], builtins.type[BaseModel]]: ...


def input(
    cls: builtins.type[BaseModel] | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
) -> (
    builtins.type[BaseModel]
    | Callable[[builtins.type[BaseModel]], builtins.type[BaseModel]]
):
    """Decorator to convert a Pydantic BaseModel directly into a GraphQL input type.

    This decorator allows you to use Pydantic models directly as GraphQL input types
    without needing to create a separate wrapper class.

    Args:
        cls: The Pydantic BaseModel class to convert
        name: The GraphQL input type name (defaults to class name)
        description: The GraphQL input type description
        directives: GraphQL directives to apply to the input type

    Returns:
        The decorated BaseModel class with GraphQL input metadata

    Example:
        @strawberry.pydantic.input
        class CreateUserInput(BaseModel):
            name: str
            age: int

        # All fields from the Pydantic model will be included in the GraphQL input type
    """

    def wrap(cls: builtins.type[BaseModel]) -> builtins.type[BaseModel]:
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
    cls: builtins.type[BaseModel],
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    include_computed: bool = False,
) -> builtins.type[BaseModel]: ...


@overload
def interface(
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    include_computed: bool = False,
) -> Callable[[builtins.type[BaseModel]], builtins.type[BaseModel]]: ...


def interface(
    cls: builtins.type[BaseModel] | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    include_computed: bool = False,
) -> (
    builtins.type[BaseModel]
    | Callable[[builtins.type[BaseModel]], builtins.type[BaseModel]]
):
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

    def wrap(cls: builtins.type[BaseModel]) -> builtins.type[BaseModel]:
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
