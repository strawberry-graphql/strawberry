"""Object type decorators for Pydantic models in Strawberry GraphQL.

This module provides decorators to convert Pydantic BaseModel classes directly
into GraphQL types, inputs, and interfaces without requiring a separate wrapper class.
"""

from __future__ import annotations

import builtins
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Callable, Optional, Union, overload

from strawberry.experimental.pydantic._compat import PydanticCompat
from strawberry.experimental.pydantic.conversion import (
    convert_strawberry_class_to_pydantic_model,
)
from strawberry.types.base import StrawberryObjectDefinition
from strawberry.types.cast import get_strawberry_type_cast
from strawberry.utils.str_converters import to_camel_case

from .fields import _get_pydantic_fields

if TYPE_CHECKING:
    from graphql import GraphQLResolveInfo

    from pydantic import BaseModel


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
    cls: type[BaseModel],
    *,
    name: Optional[str] = None,
    is_input: bool = False,
    is_interface: bool = False,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
    include_computed: bool = False,
    use_pydantic_alias: bool = True,
) -> type[BaseModel]:
    """Process a Pydantic BaseModel class and add GraphQL metadata.
    
    Args:
        cls: The Pydantic BaseModel class to process
        name: The GraphQL type name (defaults to class name)
        is_input: Whether this is an input type
        is_interface: Whether this is an interface type
        description: The GraphQL type description
        directives: GraphQL directives to apply
        all_fields: Whether to include all fields from the model
        include_computed: Whether to include computed fields
        use_pydantic_alias: Whether to use Pydantic field aliases
        
    Returns:
        The processed BaseModel class with GraphQL metadata
    """
    # Get the GraphQL type name
    name = name or to_camel_case(cls.__name__)

    # Get compatibility layer for this model
    compat = PydanticCompat.from_model(cls)
    model_fields = compat.get_model_fields(cls, include_computed=include_computed)

    # Get annotations from the class to check for strawberry.auto
    existing_annotations = getattr(cls, "__annotations__", {})

    # In direct integration, we always include all fields from the Pydantic model
    fields_set = set(model_fields.keys())
    auto_fields_set = set(model_fields.keys())  # All fields should use Pydantic types

    # Extract fields using our custom function
    fields = _get_pydantic_fields(
        cls=cls,
        original_type_annotations={},
        is_input=is_input,
        fields_set=fields_set,
        auto_fields_set=auto_fields_set,
        use_pydantic_alias=use_pydantic_alias,
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

    # Add conversion methods
    def from_pydantic(
        instance: BaseModel, extra: Optional[dict[str, Any]] = None
    ) -> BaseModel:
        """Convert a Pydantic model instance to a GraphQL-compatible instance."""
        if extra:
            # If there are extra fields, create a new instance with them
            instance_dict = compat.model_dump(instance)
            instance_dict.update(extra)
            return cls(**instance_dict)
        return instance

    def to_pydantic(self: Any, **kwargs: Any) -> BaseModel:
        """Convert a GraphQL instance back to a Pydantic model."""
        if isinstance(self, cls):
            # If it's already the right type, return it
            if not kwargs:
                return self
            # Create a new instance with the updated kwargs
            instance_dict = compat.model_dump(self)
            instance_dict.update(kwargs)
            return cls(**instance_dict)

        # If it's a different type, convert it
        return convert_strawberry_class_to_pydantic_model(self, **kwargs)

    # Add conversion methods if they don't exist
    if not hasattr(cls, "from_pydantic"):
        cls.from_pydantic = staticmethod(from_pydantic)  # type: ignore
    if not hasattr(cls, "to_pydantic"):
        cls.to_pydantic = to_pydantic  # type: ignore

    # Register the type for schema generation
    if is_input:
        cls._strawberry_input_type = cls  # type: ignore
    else:
        cls._strawberry_type = cls  # type: ignore

    return cls


@overload
def type(
    cls: type[BaseModel],
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
    include_computed: bool = False,
    use_pydantic_alias: bool = True,
) -> type[BaseModel]: ...


@overload
def type(
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
    include_computed: bool = False,
    use_pydantic_alias: bool = True,
) -> Callable[[type[BaseModel]], type[BaseModel]]: ...


def type(
    cls: Optional[type[BaseModel]] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
    include_computed: bool = False,
    use_pydantic_alias: bool = True,
) -> Union[type[BaseModel], Callable[[type[BaseModel]], type[BaseModel]]]:
    """Decorator to convert a Pydantic BaseModel directly into a GraphQL type.
    
    This decorator allows you to use Pydantic models directly as GraphQL types
    without needing to create a separate wrapper class.
    
    Args:
        cls: The Pydantic BaseModel class to convert
        name: The GraphQL type name (defaults to class name)
        description: The GraphQL type description
        directives: GraphQL directives to apply to the type
        all_fields: Whether to include all fields from the model
        include_computed: Whether to include computed fields
        use_pydantic_alias: Whether to use Pydantic field aliases
        
    Returns:
        The decorated BaseModel class with GraphQL metadata
        
    Example:
        @strawberry.pydantic.type
        class User(BaseModel):
            name: str
            age: int
            
        # All fields from the Pydantic model will be included in the GraphQL type
    """
    def wrap(cls: type[BaseModel]) -> type[BaseModel]:
        return _process_pydantic_type(
            cls,
            name=name,
            is_input=False,
            is_interface=False,
            description=description,
            directives=directives,
            include_computed=include_computed,
            use_pydantic_alias=use_pydantic_alias,
        )

    if cls is None:
        return wrap

    return wrap(cls)


@overload
def input(
    cls: type[BaseModel],
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
    use_pydantic_alias: bool = True,
) -> type[BaseModel]: ...


@overload
def input(
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
    use_pydantic_alias: bool = True,
) -> Callable[[type[BaseModel]], type[BaseModel]]: ...


def input(
    cls: Optional[type[BaseModel]] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
    use_pydantic_alias: bool = True,
) -> Union[type[BaseModel], Callable[[type[BaseModel]], type[BaseModel]]]:
    """Decorator to convert a Pydantic BaseModel directly into a GraphQL input type.
    
    This decorator allows you to use Pydantic models directly as GraphQL input types
    without needing to create a separate wrapper class.
    
    Args:
        cls: The Pydantic BaseModel class to convert
        name: The GraphQL input type name (defaults to class name)
        description: The GraphQL input type description
        directives: GraphQL directives to apply to the input type
        all_fields: Whether to include all fields from the model
        use_pydantic_alias: Whether to use Pydantic field aliases
        
    Returns:
        The decorated BaseModel class with GraphQL input metadata
        
    Example:
        @strawberry.pydantic.input
        class CreateUserInput(BaseModel):
            name: str
            age: int
            
        # All fields from the Pydantic model will be included in the GraphQL input type
    """
    def wrap(cls: type[BaseModel]) -> type[BaseModel]:
        return _process_pydantic_type(
            cls,
            name=name,
            is_input=True,
            is_interface=False,
            description=description,
            directives=directives,
            include_computed=False,  # Input types don't need computed fields
            use_pydantic_alias=use_pydantic_alias,
        )

    if cls is None:
        return wrap

    return wrap(cls)


@overload
def interface(
    cls: type[BaseModel],
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
    include_computed: bool = False,
    use_pydantic_alias: bool = True,
) -> type[BaseModel]: ...


@overload
def interface(
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
    include_computed: bool = False,
    use_pydantic_alias: bool = True,
) -> Callable[[type[BaseModel]], type[BaseModel]]: ...


def interface(
    cls: Optional[type[BaseModel]] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Optional[Sequence[object]] = (),
    include_computed: bool = False,
    use_pydantic_alias: bool = True,
) -> Union[type[BaseModel], Callable[[type[BaseModel]], type[BaseModel]]]:
    """Decorator to convert a Pydantic BaseModel directly into a GraphQL interface.
    
    This decorator allows you to use Pydantic models directly as GraphQL interfaces
    without needing to create a separate wrapper class.
    
    Args:
        cls: The Pydantic BaseModel class to convert
        name: The GraphQL interface name (defaults to class name)
        description: The GraphQL interface description
        directives: GraphQL directives to apply to the interface
        all_fields: Whether to include all fields from the model
        include_computed: Whether to include computed fields
        use_pydantic_alias: Whether to use Pydantic field aliases
        
    Returns:
        The decorated BaseModel class with GraphQL interface metadata
        
    Example:
        @strawberry.pydantic.interface
        class Node(BaseModel):
            id: str
    """
    def wrap(cls: type[BaseModel]) -> type[BaseModel]:
        return _process_pydantic_type(
            cls,
            name=name,
            is_input=False,
            is_interface=True,
            description=description,
            directives=directives,
            include_computed=include_computed,
            use_pydantic_alias=use_pydantic_alias,
        )

    if cls is None:
        return wrap

    return wrap(cls)


__all__ = ["input", "interface", "type"]
